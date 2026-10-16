from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import LoginForm, RegisterForm, UserForm, ProfileForm
from .activity import log
from .i18n import STRINGS
from .models import Banner, Category, Product, CartItem, Order, OrderItem, Profile

def _safe_next(request, default="/"):
    nxt = request.POST.get("next") or request.GET.get("next") or default
    return nxt if url_has_allowed_host_and_scheme(nxt, request.get_host()) else default

def home(request):
    sections = [(c, c.products.all()[:4]) for c in Category.objects.all()]
    return render(request, "home.html", {"banners": Banner.objects.filter(active=True), "sections": sections})

def shop(request, slug=None):
    cat = get_object_or_404(Category, slug=slug) if slug else None
    products = Product.objects.select_related("category")
    if cat:
        products = products.filter(category=cat)
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(Q(name_fa__icontains=q) | Q(name_en__icontains=q))
    return render(request, "shop.html", {"cat": cat, "products": products, "q": q})

def product_detail(request, pk):
    p = get_object_or_404(Product, pk=pk)
    related = Product.objects.filter(category=p.category).exclude(pk=pk)[:4]
    return render(request, "product.html", {"p": p, "related": related})

def set_lang(request, code):
    if code in STRINGS:
        request.session["lang"] = code
    return redirect(_safe_next(request))

# ---- auth ----
class LoginPage(LoginView):
    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.get_or_create(user=user)
        log(user, "register")
        login(request, user)
        return redirect("home")
    return render(request, "register.html", {"form": form})

@login_required
def profile(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)
    uform = UserForm(request.POST or None, instance=request.user)
    pform = ProfileForm(request.POST or None, instance=prof)
    if request.method == "POST" and uform.is_valid() and pform.is_valid():
        uform.save(); pform.save()
        log(request.user, "profile")
        messages.success(request, STRINGS[request.LANGUAGE_CODE]["saved"])
        return redirect("profile")
    return render(request, "profile.html", {"uform": uform, "pform": pform})

# ---- cart ----
@login_required
def cart(request):
    items = CartItem.objects.filter(user=request.user).select_related("product")
    return render(request, "cart.html", {"items": items})

@require_POST
def add_to_cart(request, pk):
    T = STRINGS[request.LANGUAGE_CODE]
    nxt = _safe_next(request, "/cart/")
    if not request.user.is_authenticated:
        messages.info(request, T["login_first"])
        return redirect(f"/login/?next={nxt}")
    product = get_object_or_404(Product, pk=pk)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity = min(item.quantity + 1, 99)
        item.save()
    log(request.user, "add_cart", product.name_en)
    messages.success(request, f"{product.name} — {T['added']}")
    return redirect(nxt)

@login_required
@require_POST
def update_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, user=request.user)
    try:
        qty = int(request.POST.get("qty", 1))
    except ValueError:
        qty = 1
    item.quantity = max(1, min(qty, 99))
    item.save()
    return JsonResponse({"qty": item.quantity})

@login_required
@require_POST
def remove_from_cart(request, pk):
    item = CartItem.objects.filter(pk=pk, user=request.user).select_related("product").first()
    if item:
        log(request.user, "remove_cart", item.product.name_en)
        item.delete()
    return redirect("cart")

# ---- checkout (demo) ----
@login_required
@require_POST
def checkout(request):
    ids = [i for i in request.POST.getlist("items") if i.isdigit()]
    items = CartItem.objects.filter(user=request.user, pk__in=ids)
    if not items.exists():
        messages.error(request, STRINGS[request.LANGUAGE_CODE]["select_items"])
        return redirect("cart")
    request.session["checkout_ids"] = list(items.values_list("pk", flat=True))
    log(request.user, "checkout", f"{items.count()} items")
    return redirect("gateway")

@login_required
def gateway(request):
    ids = request.session.get("checkout_ids", [])
    items = CartItem.objects.filter(user=request.user, pk__in=ids).select_related("product")
    if not items:
        return redirect("cart")
    total = sum(i.subtotal for i in items)
    if request.method == "POST":
        if request.POST.get("action") == "pay":
            with transaction.atomic():
                order = Order.objects.create(user=request.user, total=total, status="paid")
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product_name=i.product.name_en, price=i.product.price, quantity=i.quantity) for i in items])
                items.delete()
            request.session.pop("checkout_ids", None)
            log(request.user, "paid", f"order #{order.pk} — {total}")
            return redirect("order_success", pk=order.pk)
        request.session.pop("checkout_ids", None)
        log(request.user, "cancel")
        return redirect("cart")
    return render(request, "gateway.html", {"items": items, "total": total})

@login_required
def order_success(request, pk):
    return render(request, "success.html", {"order": get_object_or_404(Order, pk=pk, user=request.user)})

@login_required
def orders(request):
    return render(request, "orders.html", {"orders": request.user.orders.prefetch_related("items")})