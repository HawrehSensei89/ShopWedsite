from .models import Activity

def log(user, action, detail=""):
    Activity.objects.create(
        user=user if (user is not None and getattr(user, "is_authenticated", False)) else None,
        action=action, detail=str(detail)[:200])