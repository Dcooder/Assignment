"""Server-rendered warehouse workflows; packing stays in pure services."""

from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BoxForm, OrderBuildForm, ProductForm
from .models import Box, Order, OrderItem, Product
from .services.recommendation import recommend


def landing(request):
    return render(request, "landing.html")


def landing_or_dashboard(request):
    return dashboard(request)


def dashboard(request):
    context = {
        "product_count": Product.objects.count(),
        "box_count": Box.objects.filter(is_active=True).count(),
        "order_count": Order.objects.count(),
        "recent_orders": Order.objects.prefetch_related("items")[:5],
    }
    return render(request, "dashboard.html", context)


def product_list(request):
    query = request.GET.get("q", "")
    products = Product.objects.all()
    if query:
        products = products.filter(name__icontains=query) | products.filter(
            sku__icontains=query
        )
    return render(request, "products/list.html", {"products": products, "query": query})


def product_form(request, pk=None):
    instance = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product saved.")
        return redirect("product_list")
    context = {
        "form": form,
        "title": "Edit product" if pk else "Add product",
        "cancel_url": "product_list",
    }
    return render(request, "shared/form.html", context)


@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    messages.success(
        request,
        f"Product {'activated' if product.is_active else 'deactivated'} successfully.",
    )
    return redirect("product_list")


@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.orderitem_set.exists():
        product.is_active = False
        product.save(update_fields=["is_active", "updated_at"])
        messages.warning(
            request,
            "Product is used by historical orders, so it was safely deactivated instead of deleted.",
        )
    else:
        product.delete()
        messages.success(request, "Product deleted.")
    return redirect("product_list")


def box_list(request):
    return render(request, "boxes/list.html", {"boxes": Box.objects.all()})


def box_form(request, pk=None):
    instance = get_object_or_404(Box, pk=pk) if pk else None
    form = BoxForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Box saved.")
        return redirect("box_list")
    context = {
        "form": form,
        "title": "Edit shipping box" if pk else "Add shipping box",
        "cancel_url": "box_list",
    }
    return render(request, "shared/form.html", context)


@require_POST
def box_toggle(request, pk):
    box = get_object_or_404(Box, pk=pk)
    box.is_active = not box.is_active
    box.save()
    messages.success(request, f"Box {'activated' if box.is_active else 'deactivated'}.")
    return redirect("box_list")


@require_POST
def box_delete(request, pk):
    box = get_object_or_404(Box, pk=pk)
    if box.recommended_orders.exists():
        box.is_active = False
        box.save(update_fields=["is_active", "updated_at"])
        messages.warning(
            request,
            "Box is referenced by historical orders, so it was safely deactivated instead of deleted.",
        )
    else:
        box.delete()
        messages.success(request, "Box deleted.")
    return redirect("box_list")


def _cart(request):
    return {
        int(product_id): int(quantity)
        for product_id, quantity in request.session.get("cart", {}).items()
        if int(quantity) > 0
    }


def _set_cart(request, cart):
    request.session["cart"] = {
        str(product_id): quantity
        for product_id, quantity in cart.items()
        if quantity > 0
    }
    request.session.modified = True


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = _cart(request)
    cart[product.id] = cart.get(product.id, 0) + 1
    _set_cart(request, cart)
    messages.success(request, f"{product.name} added to the order cart.")
    return redirect(request.POST.get("next") or "product_list")


def cart_detail(request):
    cart = _cart(request)
    products = Product.objects.filter(id__in=cart, is_active=True)
    rows = [{"product": product, "quantity": cart[product.id]} for product in products]
    return render(request, "orders/cart.html", {"cart_rows": rows})


@require_POST
def cart_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        quantity = int(request.POST.get("quantity", "0"))
    except ValueError:
        quantity = 0
    cart = _cart(request)
    if quantity > 0 and product.is_active:
        cart[product.id] = quantity
    else:
        cart.pop(product.id, None)
    _set_cart(request, cart)
    return redirect("cart_detail")


def order_list(request):
    return render(
        request,
        "orders/list.html",
        {"orders": Order.objects.prefetch_related("items", "recommended_box")},
    )


def _snapshot(product):
    return {
        "name": product.name,
        "sku": product.sku,
        "length": str(product.length),
        "width": str(product.width),
        "height": str(product.height),
        "dimension_unit": product.dimension_unit,
        "display_dimensions": product.displayed_dimensions,
        "weight": str(product.weight),
    }


def _serialize_packing(result):
    placements = []
    for placement in result["placements"]:
        placements.append(
            {
                **placement,
                "x": str(placement["x"]),
                "y": str(placement["y"]),
                "z": str(placement["z"]),
                "dimensions": [str(value) for value in placement["dimensions"]],
            }
        )
    return {"placements": placements, "nodes_visited": result.get("nodes_visited", 0)}


def order_create(request):
    cart = _cart(request)
    if request.method == "GET":
        cart_products = Product.objects.filter(id__in=cart, is_active=True)
        initial_items = [
            {"product_id": product.id, "quantity": cart[product.id]}
            for product in cart_products
        ]
        form = OrderBuildForm(initial={"items": initial_items})
    else:
        form = OrderBuildForm(request.POST)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            order = Order.objects.create()
            for product, quantity in form.cleaned_data["items"]:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    product_snapshot=_snapshot(product),
                )
            order.total_weight = sum(
                (
                    Decimal(item.product_snapshot["weight"]) * item.quantity
                    for item in order.items.all()
                ),
                Decimal("0"),
            )
            selected, evaluations = recommend(
                order.items.all(), Box.objects.filter(is_active=True)
            )
            order.evaluation = evaluations
            if selected:
                box, result = selected
                order.status = Order.Status.RECOMMENDED
                order.recommended_box = box
                order.selected_box_cost = box.shipping_cost
                order.recommended_box_snapshot = {
                    "code": box.code,
                    "length": str(box.length),
                    "width": str(box.width),
                    "height": str(box.height),
                    "dimension_unit": box.dimension_unit,
                    "display_dimensions": box.displayed_dimensions,
                    "max_weight": str(box.max_weight),
                    "shipping_cost": str(box.shipping_cost),
                }
                order.packing_result = _serialize_packing(result)
            order.save()
            _set_cart(request, {})
        return redirect("order_detail", pk=order.pk)
    return render(
        request,
        "orders/create.html",
        {
            "form": form,
            "products": Product.objects.filter(is_active=True),
            "cart_items": form.initial.get("items", []),
        },
    )


def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)
    return render(request, "orders/detail.html", {"order": order})
