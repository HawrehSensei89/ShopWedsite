from django import template
from django.utils.translation import get_language
register = template.Library()
FA = str.maketrans("0123456789,", "۰۱۲۳۴۵۶۷۸۹٬")

@register.filter
def money(value):
    s = f"{int(value):,}"
    return s.translate(FA) if (get_language() or "fa").startswith("fa") else s
