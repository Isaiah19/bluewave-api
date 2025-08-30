from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Product, Order, OrderItem, Subscription
import decimal
import requests


def home(request):
    return render(request, "home.html")


def product_list(request):
    products = Product.objects.all().order_by("-created_at")
    return render(request, "product_list.html", {"products": products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "product_detail.html", {"product": product})


@login_required
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order_id = request.session.get("order_id")

    if order_id:
        order = Order.objects.get(pk=order_id)
    else:
        order = Order.objects.create(user=request.user, total=decimal.Decimal("0.00"))
        request.session["order_id"] = order.id

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        line_total=product.price,
    )

    order.total = (order.total or decimal.Decimal("0.00")) + product.price
    order.save()

    messages.success(request, f"Added {product.name} to cart.")
    return redirect("cart_view")


@login_required
def cart_view(request):
    order = None
    oid = request.session.get("order_id")
    if oid:
        order = Order.objects.filter(id=oid).first()
    return render(request, "cart.html", {"order": order})


@login_required
def checkout(request):
    """Simple demo checkout: activates subscriptions and clears the cart."""
    oid = request.session.get("order_id")
    if not oid:
        messages.warning(request, "Your cart is empty.")
        return redirect("product_list")

    order = Order.objects.get(id=oid)
    for item in order.items.all():
        if item.product.is_subscription:
            Subscription.objects.get_or_create(
                user=request.user,
                product=item.product,
                defaults={"active": True},
            )

    # Clear cart
    if "order_id" in request.session:
        del request.session["order_id"]

    messages.success(
        request,
        "Checkout complete. Subscriptions (if any) are now active.",
    )
    return redirect("dashboard")


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@login_required
def request_jwt(request):
    """Call the Flask API /auth/token and display it on the dashboard."""
    api_base = getattr(settings, "BLUEWAVE_API_BASE", "http://127.0.0.1:8000").rstrip("/")
    try:
        r = requests.post(f"{api_base}/auth/token", timeout=5)
        r.raise_for_status()
        token = r.json().get("access_token")
        if not token:
            raise ValueError("No access_token in response")
        messages.success(request, "New API token issued.")
        return render(request, "dashboard.html", {"api_token": token, "BLUEWAVE_API_BASE": api_base})
    except Exception as e:
        messages.error(request, f"Failed to get token from {api_base}: {e}")
        return redirect("dashboard")

