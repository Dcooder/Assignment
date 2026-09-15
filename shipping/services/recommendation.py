from decimal import Decimal

from .packing import Item, evaluate

REASON_LABELS = {
    "weight_exceeded": "Maximum weight exceeded.",
    "volume_exceeded": "Total item volume exceeds the box volume.",
    "item_does_not_fit": (
        "At least one product cannot fit in the internal dimensions, even "
        "after rotation."
    ),
    "packing_failed": (
        "The products could not be packed together within the internal "
        "dimensions."
    ),
}


def build_items(order_items):
    items = []
    for order_item in order_items:
        snapshot = order_item.product_snapshot
        dimensions = tuple(
            Decimal(snapshot[field]) for field in ("length", "width", "height")
        )
        for number in range(order_item.quantity):
            items.append(
                Item(
                    f"{snapshot['sku']}#{number + 1}",
                    dimensions,
                    Decimal(snapshot["weight"]),
                )
            )
    return items


def recommend(order_items, boxes):
    items = build_items(order_items)
    if not items:
        return None, []

    evaluations = []
    suitable = []

    for box in boxes:
        if not box.is_active:
            continue

        result = evaluate(items, (box.length, box.width, box.height), box.max_weight)
        entry = {
            "box_id": box.id,
            "box_code": box.code,
            "success": result["success"],
            "reason": result["reason"],
            "reason_label": (
                "Suitable." if result["success"] else REASON_LABELS[result["reason"]]
            ),
        }
        evaluations.append(entry)

        if result["success"]:
            unused = Decimal(box.length) * Decimal(box.width) * Decimal(
                box.height
            ) - sum((item.volume for item in items), Decimal("0"))
            suitable.append((box.shipping_cost, unused, box.code, box, result))

    if not suitable:
        return None, evaluations

    _, _, _, box, result = min(suitable, key=lambda candidate: candidate[:3])
    return (box, result), evaluations
