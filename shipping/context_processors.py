def cart_count(request):
    return {
        "cart_count": sum(
            int(quantity) for quantity in request.session.get("cart", {}).values()
        )
    }
