from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import get_language

def _loc(obj, base):
    suffix = "fa" if (get_language() or "fa").startswith("fa") else "en"
    return getattr(obj, f"{base}_{suffix}") or getattr(obj, f"{base}_fa")

class Category(models.Model):
    slug = models.SlugField(unique=True)
    name_fa = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80)
    icon = models.CharField(max_length=40, default="ri-shopping-bag-line", help_text="Remix Icon class")
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "categories"
    @property
    def name(self): return _loc(self, "name")
    def __str__(self): return self.name_en

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name_fa = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)
    desc_fa = models.TextField(blank=True)
    desc_en = models.TextField(blank=True)
    price = models.PositiveIntegerField(help_text="Toman")
    image = models.ImageField(upload_to="products/", blank=True)
    emoji = models.CharField(max_length=8, default="🛍️", help_text="Shown when there is no image")
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created", "-id"]
    @property
    def name(self): return _loc(self, "name")
    @property
    def desc(self): return _loc(self, "desc")
    def __str__(self): return self.name_en

class Banner(models.Model):
    title_fa = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    subtitle_fa = models.CharField(max_length=200, blank=True)
    subtitle_en = models.CharField(max_length=200, blank=True)
    button_fa = models.CharField(max_length=40, blank=True)
    button_en = models.CharField(max_length=40, blank=True)
    link = models.CharField(max_length=200, default="/shop/", validators=[RegexValidator(r"^(/|https?://)", "Link must start with / or http(s)://")])
    emoji = models.CharField(max_length=8, default="🔥")
    image = models.ImageField(upload_to="banners/", blank=True)
    theme = models.CharField(max_length=10, default="red", choices=[("red", "red"), ("green", "green"), ("dark", "dark")])
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    class Meta:
        ordering = ["order", "id"]
    @property
    def title(self): return _loc(self, "title")
    @property
    def subtitle(self): return _loc(self, "subtitle")
    @property
    def button(self): return _loc(self, "button")
    def __str__(self): return self.title_en

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    def __str__(self): return self.user.username

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    class Meta:
        unique_together = ("user", "product")
    @property
    def subtotal(self): return self.product.price * self.quantity

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    total = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, default="paid")
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created"]

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_name = models.CharField(max_length=150)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

class Visit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="visits")
    session_key = models.CharField(max_length=40, db_index=True)
    path = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
        ordering = ["-created"]

class Activity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities")
    action = models.CharField(max_length=30)
    detail = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "activities"
