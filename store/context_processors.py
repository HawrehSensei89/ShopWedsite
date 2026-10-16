from django.db.models import Sum
from .i18n import STRINGS
from .models import Category, CartItem

def site(request):
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    count = 0
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).aggregate(n=Sum("quantity"))["n"] or 0
    return {"T": STRINGS[lang], "lang": lang, "dir": "rtl" if lang == "fa" else "ltr",
            "nav_categories": Category.objects.all(), "cart_count": count}
