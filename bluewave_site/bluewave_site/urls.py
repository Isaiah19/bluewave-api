from django.contrib import admin
from django.urls import path
from store import views as store_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", store_views.home, name="home"),
    path("products/", store_views.product_list, name="product_list"),
    path("products/<int:pk>/", store_views.product_detail, name="product_detail"),
    path("cart/add/<int:pk>/", store_views.cart_add, name="cart_add"),
    path("cart/", store_views.cart_view, name="cart_view"),
    path("checkout/", store_views.checkout, name="checkout"),
    path("dashboard/", store_views.dashboard, name="dashboard"),
    path("jwt/request/", store_views.request_jwt, name="request_jwt"),

    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
]

