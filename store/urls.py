from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, panel
urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("shop/<slug:slug>/", views.shop, name="category"),
    path("product/<int:pk>/", views.product_detail, name="product"),
    path("lang/<str:code>/", views.set_lang, name="set_lang"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:pk>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("gateway/", views.gateway, name="gateway"),
    path("order/<int:pk>/", views.order_success, name="order_success"),
    path("orders/", views.orders, name="orders"),
    path("login/", views.LoginPage.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("panel/", panel.dashboard, name="panel"),
    path("panel/<str:entity>/", panel.entity_list, name="panel_list"),
    path("panel/<str:entity>/add/", panel.entity_edit, name="panel_add"),
    path("panel/<str:entity>/<int:pk>/edit/", panel.entity_edit, name="panel_edit"),
    path("panel/<str:entity>/<int:pk>/delete/", panel.entity_delete, name="panel_delete"),
]