from django.contrib.auth.signals import user_logged_in, user_logged_out
from .activity import log

def _in(sender, request, user, **kw): log(user, "login")
def _out(sender, request, user, **kw):
    if user is not None: log(user, "logout")

def connect():
    user_logged_in.connect(_in, dispatch_uid="shop_login")
    user_logged_out.connect(_out, dispatch_uid="shop_logout")