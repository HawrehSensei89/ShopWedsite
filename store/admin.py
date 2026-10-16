from django.contrib import admin
from .models import *
admin.site.register([Category, Banner, Profile, CartItem])
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_fa", "category", "price")
    list_filter = ("category",)
    search_fields = ("name_en", "name_fa")
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total", "status", "created")
    inlines = [OrderItemInline]

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
admin.site.unregister(User)
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
admin.site.site_header = "Shop admin"
