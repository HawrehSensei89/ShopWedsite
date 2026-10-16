from django.utils import translation

class LangMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        lang = request.session.get("lang", "fa")
        if lang not in ("fa", "en"):
            lang = "fa"
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response

import re
from .models import Visit

_SKIP = ("/admin", "/panel", "/static", "/media", "/lang", "/favicon")
_BOT = re.compile(r"bot|crawl|spider|slurp|preview|facebookexternalhit", re.I)

class VisitMiddleware:
    """Records one row per HTML page view (not admin/panel/static, not bots)."""
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        response = self.get_response(request)
        try:
            if (request.method == "GET" and response.status_code == 200
                    and not request.path.startswith(_SKIP)
                    and "text/html" in response.get("Content-Type", "")
                    and not _BOT.search(request.META.get("HTTP_USER_AGENT", ""))):
                if not request.session.session_key:
                    request.session.create()
                Visit.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key or "", path=request.path[:200])
        except Exception:
            pass
        return response