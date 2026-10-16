from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

ADMIN_EMAIL = "admin@gmai.com"
ADMIN_PASSWORD = "Admin"

class Command(BaseCommand):
    help = "Create (or reset) the site administrator account"
    def handle(self, *a, **k):
        u, _ = User.objects.get_or_create(username=ADMIN_EMAIL, defaults={"email": ADMIN_EMAIL})
        u.email = ADMIN_EMAIL
        u.is_staff = u.is_superuser = u.is_active = True
        u.set_password(ADMIN_PASSWORD)  # stored hashed, never as plain text
        u.save()
        self.stdout.write(self.style.SUCCESS(f"Admin ready: {ADMIN_EMAIL}"))
