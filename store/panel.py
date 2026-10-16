"""Custom staff-only management panel (/panel/) that reuses the shop's theme, fonts and language switch."""
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from .i18n import STRINGS
from .models import Activity, Banner, Category, Order, OrderItem, Product, Visit
from .templatetags.shop_extras import FA, money


def staff_required(view):
    @wraps(view)
    def wrapper(request, *a, **k):
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *a, **k)
    return wrapper


def _fa():
    return (get_language() or "fa").startswith("fa")

def num(n):
    return money(n or 0)

def digits(s):
    return s.translate(FA) if _fa() else s

def when(d):
    return digits(timezone.localtime(d).strftime("%Y/%m/%d %H:%M"))

def who(u, T):
    return u.email if u else T["guest"]


# label (fa, en) for form fields
LABELS = {
    "first_name": ("نام", "First name"), "last_name": ("نام خانوادگی", "Last name"),
    "is_active": ("فعال", "Active"), "is_staff": ("دسترسی ادمین", "Staff (admin access)"),
    "slug": ("نامک (slug)", "Slug"), "name_fa": ("نام فارسی", "Persian name"), "name_en": ("نام انگلیسی", "English name"),
    "icon": ("آیکون (Remix Icon)", "Icon (Remix Icon class)"), "order": ("ترتیب نمایش", "Display order"),
    "category": ("دسته‌بندی", "Category"), "desc_fa": ("توضیحات فارسی", "Persian description"),
    "desc_en": ("توضیحات انگلیسی", "English description"), "price": ("قیمت (تومان)", "Price (Toman)"),
    "image": ("تصویر", "Image"), "emoji": ("ایموجی (بدون تصویر)", "Emoji (when no image)"),
    "title_fa": ("عنوان فارسی", "Persian title"), "title_en": ("عنوان انگلیسی", "English title"),
    "subtitle_fa": ("زیرعنوان فارسی", "Persian subtitle"), "subtitle_en": ("زیرعنوان انگلیسی", "English subtitle"),
    "link": ("مقصد دکمه (لینک)", "Button destination (link)"),
    "button_fa": ("متن دکمه (فارسی)", "Button text (Persian)"), "button_en": ("متن دکمه (انگلیسی)", "Button text (English)"), "theme": ("تم رنگی", "Color theme"), "active": ("فعال", "Active"),
}

ENT = {
    "users": dict(
        model=User, title="p_users", icon="ri-user-3-line", add=False, edit=True, delete=True,
        qs=lambda: User.objects.annotate(n=Count("orders")).order_by("-date_joined"),
        search=("email", "first_name", "last_name"), form=("first_name", "last_name", "is_active", "is_staff"),
        cols=[("email", lambda o, T: o.email), ("col_name", lambda o, T: o.get_full_name() or "—"),
              ("col_joined", lambda o, T: when(o.date_joined)),
              ("col_role", lambda o, T: T["role_admin"] if o.is_staff else T["role_user"]),
              ("col_status", lambda o, T: T["active"] if o.is_active else T["inactive"]),
              ("orders", lambda o, T: num(o.n))]),
    "categories": dict(
        model=Category, title="categories", icon="ri-folder-3-line", add=True, edit=True, delete=True,
        qs=lambda: Category.objects.annotate(n=Count("products")).order_by("order", "id"), search=("name_fa", "name_en", "slug"),
        form=("slug", "name_fa", "name_en", "icon", "order"),
        cols=[("col_name_fa", lambda o, T: o.name_fa), ("col_name_en", lambda o, T: o.name_en),
              ("col_slug", lambda o, T: o.slug), ("col_products", lambda o, T: num(o.n))]),
    "products": dict(
        model=Product, title="p_products", icon="ri-shopping-bag-3-line", add=True, edit=True, delete=True,
        qs=lambda: Product.objects.select_related("category"), search=("name_fa", "name_en"),
        form=("category", "name_fa", "name_en", "desc_fa", "desc_en", "price", "image", "emoji"),
        cols=[("col_name", lambda o, T: f"{o.emoji} {o.name}"), ("col_category", lambda o, T: o.category.name),
              ("col_price", lambda o, T: f"{num(o.price)} {T['toman']}"), ("col_time", lambda o, T: when(o.created))]),
    "banners": dict(
        model=Banner, title="p_banners", icon="ri-slideshow-3-line", add=True, edit=True, delete=True,
        qs=lambda: Banner.objects.all(), search=("title_fa", "title_en"),
        form=("title_fa", "title_en", "subtitle_fa", "subtitle_en", "button_fa", "button_en", "link", "image", "emoji", "theme", "order", "active"),
        cols=[("col_name", lambda o, T: f"{o.emoji} {o.title}"), ("col_link", lambda o, T: o.link), ("col_order", lambda o, T: num(o.order)),
              ("col_theme", lambda o, T: o.theme), ("col_status", lambda o, T: T["active"] if o.active else T["inactive"])]),
    "orders": dict(
        model=Order, title="orders", icon="ri-receipt-line", add=False, edit=False, delete=True,
        qs=lambda: Order.objects.select_related("user"), search=("user__email",),
        cols=[("col_id", lambda o, T: "#" + num(o.pk)), ("col_user", lambda o, T: who(o.user, T)),
              ("col_total", lambda o, T: f"{num(o.total)} {T['toman']}"),
              ("col_status", lambda o, T: T["status_paid"] if o.status == "paid" else o.status),
              ("col_time", lambda o, T: when(o.created))]),
    "visits": dict(
        model=Visit, title="p_visits", icon="ri-eye-line", add=False, edit=False, delete=False,
        qs=lambda: Visit.objects.select_related("user"), search=("path", "user__email"),
        cols=[("col_time", lambda o, T: when(o.created)), ("col_user", lambda o, T: who(o.user, T)),
              ("col_page", lambda o, T: o.path)]),
    "activity": dict(
        model=Activity, title="p_activity", icon="ri-pulse-line", add=False, edit=False, delete=False,
        qs=lambda: Activity.objects.select_related("user"), search=("user__email", "detail"),
        cols=[("col_time", lambda o, T: when(o.created)), ("col_user", lambda o, T: who(o.user, T)),
              ("col_action", lambda o, T: T.get("act_" + o.action, o.action)), ("col_detail", lambda o, T: o.detail or "—")]),
}
NAV = [("dashboard", "p_dashboard", "ri-dashboard-line")] + [(k, v["title"], v["icon"]) for k, v in ENT.items()]


def _T(request):
    return STRINGS[request.LANGUAGE_CODE]

def _ctx(request, section, **extra):
    return {"section": section, "nav": NAV, **extra}


@staff_required
def dashboard(request):
    T = _T(request)
    now = timezone.now()
    today = timezone.localdate()
    start = today - timedelta(days=6)
    paid = Order.objects.filter(status="paid")
    revenue = paid.aggregate(s=Sum("total"))["s"] or 0
    n_orders = paid.count()
    rev_today = paid.filter(created__date=today).aggregate(s=Sum("total"))["s"] or 0
    visits = Visit.objects
    week_ago = now - timedelta(days=7)

    rev_by = {r["d"]: r["s"] for r in paid.filter(created__date__gte=start).annotate(d=TruncDate("created"))
              .values("d").annotate(s=Sum("total"))}
    vis_by = {r["d"]: r["n"] for r in visits.filter(created__date__gte=start).annotate(d=TruncDate("created"))
              .values("d").annotate(n=Count("id"))}
    days = []
    for i in range(7):
        d = start + timedelta(days=i)
        days.append({"label": digits(d.strftime("%m/%d")), "rev": rev_by.get(d, 0), "vis": vis_by.get(d, 0)})
    mr = max((d["rev"] for d in days), default=0) or 1
    mv = max((d["vis"] for d in days), default=0) or 1
    for d in days:
        d["rev_pct"] = round(d["rev"] / mr * 100)
        d["vis_pct"] = round(d["vis"] / mv * 100)
        d["rev_txt"] = num(d["rev"]); d["vis_txt"] = num(d["vis"])

    top = list(OrderItem.objects.values("product_name").annotate(q=Sum("quantity")).order_by("-q")[:5])
    names = {p.name_en: p.name for p in Product.objects.filter(name_en__in=[t["product_name"] for t in top])}
    for t in top:
        t["label"] = names.get(t["product_name"], t["product_name"]); t["q_txt"] = num(t["q"])

    stats = [
        ("ri-group-line", "st_users", num(User.objects.count()), "red"),
        ("ri-user-add-line", "st_new_users", num(User.objects.filter(date_joined__gte=week_ago).count()), "green"),
        ("ri-money-dollar-circle-line", "st_revenue", f"{num(revenue)} {T['toman']}", "red"),
        ("ri-line-chart-line", "st_revenue_today", f"{num(rev_today)} {T['toman']}", "green"),
        ("ri-receipt-line", "st_orders", num(n_orders), "red"),
        ("ri-scales-3-line", "st_avg", f"{num(revenue // n_orders if n_orders else 0)} {T['toman']}", "green"),
        ("ri-eye-line", "st_visits_today", num(visits.filter(created__date=today).count()), "red"),
        ("ri-calendar-line", "st_visits_7", num(visits.filter(created__gte=week_ago).count()), "green"),
        ("ri-bar-chart-2-line", "st_visits_total", num(visits.count()), "red"),
        ("ri-user-search-line", "st_unique", num(visits.filter(created__gte=week_ago).values("session_key").distinct().count()), "green"),
        ("ri-wifi-line", "st_online", num(visits.filter(created__gte=now - timedelta(minutes=5)).values("session_key").distinct().count()), "red"),
    ]
    def rows(qs, fields):
        return [[fn(o, T) for fn in fields] for o in qs]
    recent_act = rows(Activity.objects.select_related("user")[:8], [
        lambda o, T: when(o.created), lambda o, T: who(o.user, T), lambda o, T: T.get("act_" + o.action, o.action)])
    recent_orders = rows(Order.objects.select_related("user")[:5], [
        lambda o, T: "#" + num(o.pk), lambda o, T: who(o.user, T), lambda o, T: f"{num(o.total)} {T['toman']}"])
    return render(request, "panel/dashboard.html", _ctx(
        request, "dashboard", stats=stats, days=days, top=top, recent_act=recent_act, recent_orders=recent_orders))


def _entity(entity):
    c = ENT.get(entity)
    if not c:
        raise Http404
    return c


@staff_required
def entity_list(request, entity):
    c = _entity(entity)
    T = _T(request)
    qs = c["qs"]()
    q = request.GET.get("q", "").strip()
    if q and c["search"]:
        cond = Q()
        for f in c["search"]:
            cond |= Q(**{f + "__icontains": q})
        qs = qs.filter(cond)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    rows = [{"pk": o.pk, "cells": [fn(o, T) for _, fn in c["cols"]]} for o in page]
    return render(request, "panel/list.html", _ctx(
        request, entity, entity=entity, c=c, headers=[T[h] for h, _ in c["cols"]], rows=rows, page=page, q=q))


@staff_required
def entity_edit(request, entity, pk=None):
    c = _entity(entity)
    if (pk is None and not c["add"]) or (pk is not None and not c["edit"]):
        raise PermissionDenied
    obj = get_object_or_404(c["model"], pk=pk) if pk else None
    fields = c["form"]
    if entity == "users" and obj == request.user:
        fields = tuple(f for f in fields if f not in ("is_active", "is_staff"))
    Form = modelform_factory(c["model"], fields=fields)
    form = Form(request.POST or None, request.FILES or None, instance=obj)
    idx = 0 if _fa() else 1
    for name, field in form.fields.items():
        field.label = LABELS.get(name, (name, name))[idx]
        field.help_text = ""
        if name == "image" and entity == "banners":
            field.help_text = "1600×600 px" if not _fa() else "پیشنهاد: ۱۶۰۰×۶۰۰ پیکسل"
        if name == "link":
            field.widget.attrs.update({"list": "link-options", "dir": "ltr", "placeholder": "/shop/phones/"})
        if name in ("button_fa", "button_en"):
            field.help_text = "اختیاری" if _fa() else "Optional"
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _T(request)["saved_ok"])
        return redirect("panel_list", entity=entity)
    link_options = []
    if entity == "banners":
        link_options = [("/", _T(request)["home"]), ("/shop/", _T(request)["all_products"])]
        link_options += [(f"/shop/{x.slug}/", x.name) for x in Category.objects.all()]
        link_options += [(f"/product/{x.pk}/", x.name) for x in Product.objects.all()[:50]]
    return render(request, "panel/form.html", _ctx(request, entity, entity=entity, c=c, form=form, obj=obj, link_options=link_options))


@staff_required
@require_POST
def entity_delete(request, entity, pk):
    c = _entity(entity)
    if not c["delete"]:
        raise PermissionDenied
    obj = get_object_or_404(c["model"], pk=pk)
    if entity == "users" and (obj == request.user or obj.is_superuser):
        messages.error(request, _T(request)["cannot_delete_self"])
    else:
        obj.delete()
        messages.success(request, _T(request)["deleted_ok"])
    return redirect("panel_list", entity=entity)
