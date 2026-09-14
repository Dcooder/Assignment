from decimal import Decimal
import json
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Box, Order, OrderItem, Product
from .services.packing import (
    Item,
    Space,
    evaluate,
    orientations,
    pack,
    prune_spaces,
    split_space,
)
from .services.recommendation import recommend
from .forms import ProductForm

D = Decimal


def product(**changes):
    values = dict(
        name="Widget",
        sku="W-1",
        length=D("2"),
        width=D("2"),
        height=D("2"),
        weight=D("1"),
    )
    values.update(changes)
    return Product(**values)


def box(**changes):
    values = dict(
        code="BOX",
        length=D("10"),
        width=D("10"),
        height=D("10"),
        max_weight=D("10"),
        shipping_cost=D("20"),
    )
    values.update(changes)
    return Box(**values)


class ModelValidationTests(TestCase):
    def test_valid_product(self):
        product().full_clean()

    def test_blank_name_rejected(self):
        with self.assertRaises(ValidationError):
            product(name=" ").full_clean()

    def test_duplicate_sku_rejected(self):
        product().save()
        with self.assertRaises(ValidationError):
            product(name="Other").full_clean()

    def test_non_positive_dimensions_rejected(self):
        for value in (D("0"), D("-1")):
            with self.assertRaises(ValidationError):
                product(length=value).full_clean()

    def test_non_positive_weight_rejected(self):
        for value in (D("0"), D("-1")):
            with self.assertRaises(ValidationError):
                product(weight=value).full_clean()

    def test_valid_box_and_free_cost(self):
        box(shipping_cost=D("0")).full_clean()

    def test_box_bad_capacity_and_cost_rejected(self):
        for changes in (
            {"max_weight": D("0")},
            {"max_weight": D("-1")},
            {"shipping_cost": D("-1")},
            {"height": D("0")},
        ):
            with self.assertRaises(ValidationError):
                box(**changes).full_clean()

    def test_duplicate_box_code_rejected(self):
        box().save()
        with self.assertRaises(ValidationError):
            box(length=D("9")).full_clean()

    def test_order_item_quantity_rejected(self):
        order = Order.objects.create()
        for quantity in (0, -1):
            with self.assertRaises(ValidationError):
                OrderItem(order=order, quantity=quantity).full_clean()


class PackingTests(TestCase):
    def item(self, dims, weight="1", key="i"):
        return Item(key, tuple(D(str(x)) for x in dims), D(weight))

    def test_exact_fit(self):
        self.assertTrue(
            pack([self.item((2, 3, 4))], (D("2"), D("3"), D("4")))["success"]
        )

    def test_larger_dimension_fails(self):
        self.assertEqual(
            pack([self.item((2.1, 3, 4))], (D("2"), D("3"), D("4")))["reason"],
            "item_does_not_fit",
        )

    def test_rotation_fit(self):
        self.assertTrue(
            pack([self.item((4, 2, 3))], (D("2"), D("3"), D("4")))["success"]
        )

    def test_rotation_no_fit(self):
        self.assertFalse(
            pack([self.item((5, 2, 2))], (D("4"), D("4"), D("4")))["success"]
        )

    def test_duplicate_dimension_orientations(self):
        self.assertEqual(len(orientations((D("2"), D("2"), D("3")))), 3)

    def test_weight_boundary(self):
        item = self.item((1, 1, 1), "5")
        self.assertTrue(evaluate([item], (D("2"),) * 3, D("5"))["success"])
        self.assertEqual(
            evaluate([item], (D("2"),) * 3, D("4.999"))["reason"], "weight_exceeded"
        )

    def test_volume_rejection(self):
        self.assertEqual(
            evaluate(
                [self.item((2, 2, 2)), self.item((2, 2, 2))], (D("2"),) * 3, D("9")
            )["reason"],
            "volume_exceeded",
        )

    def test_volume_is_not_proof_of_fit(self):
        result = evaluate(
            [self.item((2, 2, 2), key="a"), self.item((2, 2, 2), key="b")],
            (D("3"), D("3"), D("2")),
            D("9"),
        )
        self.assertEqual(result["reason"], "packing_failed")

    def test_identical_items_fit(self):
        self.assertTrue(
            pack(
                [self.item((2, 2, 2), key="a"), self.item((2, 2, 2), key="b")],
                (D("4"), D("2"), D("2")),
            )["success"]
        )

    def test_mixed_items_fit(self):
        self.assertTrue(
            pack(
                [self.item((3, 2, 2), key="a"), self.item((1, 2, 2), key="b")],
                (D("4"), D("2"), D("2")),
            )["success"]
        )

    def test_result_is_deterministic(self):
        items = [self.item((2, 1, 1), key="b"), self.item((1, 2, 1), key="a")]
        self.assertEqual(
            pack(items, (D("3"), D("2"), D("1"))), pack(items, (D("3"), D("2"), D("1")))
        )

    def test_split_creates_disjoint_spaces(self):
        spaces = split_space(
            Space(D("0"), D("0"), D("0"), D("4"), D("4"), D("4")),
            (D("2"), D("2"), D("2")),
        )
        self.assertTrue(all(s.volume > 0 for s in spaces))
        for a in spaces:
            for b in spaces:
                if a != b:
                    self.assertTrue(
                        a.x + a.length <= b.x
                        or b.x + b.length <= a.x
                        or a.y + a.width <= b.y
                        or b.y + b.width <= a.y
                        or a.z + a.height <= b.z
                        or b.z + b.height <= a.z
                    )

    def test_pruning_removes_contained_space(self):
        outer = Space(D(0), D(0), D(0), D(3), D(3), D(3))
        inner = Space(D(1), D(1), D(1), D(1), D(1), D(1))
        self.assertEqual(prune_spaces((outer, inner)), (outer,))


class RecommendationTests(TestCase):
    def make_order_item(self, dims=(2, 2, 2), weight="1", quantity=1):
        order = Order.objects.create()
        p = product()
        p.save()
        return OrderItem.objects.create(
            order=order,
            product=p,
            quantity=quantity,
            product_snapshot={
                "name": p.name,
                "sku": p.sku,
                "length": str(dims[0]),
                "width": str(dims[1]),
                "height": str(dims[2]),
                "weight": weight,
            },
        )

    def test_cheapest_suitable_selected(self):
        item = self.make_order_item()
        cheap = box(code="C", shipping_cost=D("5"))
        expensive = box(code="E", shipping_cost=D("8"))
        cheap.save()
        expensive.save()
        self.assertEqual(recommend([item], [expensive, cheap])[0][0], cheap)

    def test_equal_cost_uses_unused_volume_then_code(self):
        item = self.make_order_item()
        small = box(
            code="Z", length=D("3"), width=D("3"), height=D("3"), shipping_cost=D("5")
        )
        large = box(code="A", shipping_cost=D("5"))
        small.save()
        large.save()
        self.assertEqual(recommend([item], [large, small])[0][0], small)

    def test_ineligible_box_rejected_and_inactive_ignored(self):
        item = self.make_order_item(weight="9")
        invalid = box(code="W", max_weight=D("2"))
        inactive = box(code="I", is_active=False, shipping_cost=D("1"))
        valid = box(code="V", max_weight=D("10"))
        invalid.save()
        inactive.save()
        valid.save()
        choice, evaluation = recommend([item], [invalid, inactive, valid])
        self.assertEqual(choice[0], valid)
        self.assertEqual(
            next(row for row in evaluation if row["box_code"] == "W")["reason"],
            "weight_exceeded",
        )
        self.assertNotIn("I", [row["box_code"] for row in evaluation])

    def test_no_suitable(self):
        item = self.make_order_item(dims=(20, 2, 2))
        b = box()
        b.save()
        choice, evaluation = recommend([item], [b])
        self.assertIsNone(choice)
        self.assertIn("cannot fit", evaluation[0]["reason_label"])


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("operator", password="safe-password")
        self.client.force_login(self.user)
        self.product = product()
        self.product.save()
        self.box = box()
        self.box.save()

    def test_dashboard_and_empty_orders(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Products")
        self.assertContains(self.client.get(reverse("order_list")), "No orders yet")

    def test_product_form_error(self):
        response = self.client.post(
            reverse("product_create"),
            {
                "name": "",
                "sku": "bad",
                "length": "1",
                "width": "1",
                "height": "1",
                "weight": "1",
            },
        )
        self.assertContains(response, "This field is required")

    def test_complete_order_workflow_persists_recommendation(self):
        response = self.client.post(
            reverse("order_create"),
            {"items": json.dumps([{"product_id": self.product.id, "quantity": 2}])},
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.status, Order.Status.RECOMMENDED)
        self.assertEqual(order.total_weight, D("2"))
        self.assertTrue(order.packing_result["placements"])
        detail = self.client.get(reverse("order_detail", args=[order.pk]))
        self.assertContains(detail, self.box.code)
        self.assertContains(detail, "packing-canvas")

    def test_empty_and_inactive_order_rejected(self):
        self.assertContains(
            self.client.post(reverse("order_create"), {"items": "[]"}),
            "Add at least one",
        )
        self.product.is_active = False
        self.product.save()
        self.assertContains(
            self.client.post(
                reverse("order_create"),
                {"items": json.dumps([{"product_id": self.product.id, "quantity": 1}])},
            ),
            "Only active products",
        )

    def test_no_solution_flow(self):
        self.box.max_weight = D("0.5")
        self.box.save()
        response = self.client.post(
            reverse("order_create"),
            {"items": json.dumps([{"product_id": self.product.id, "quantity": 1}])},
            follow=True,
        )
        self.assertContains(response, "No suitable box was found")
        self.assertContains(response, "Maximum weight exceeded")

    def test_unauthenticated_users_can_use_the_app(self):
        self.client.logout()
        self.assertContains(self.client.get(reverse("dashboard")), "Products")
        self.assertEqual(self.client.get(reverse("product_list")).status_code, 200)

    def test_cart_add_update_and_checkout(self):
        self.client.post(reverse("cart_add", args=[self.product.pk]))
        self.client.post(reverse("cart_add", args=[self.product.pk]))
        self.assertContains(self.client.get(reverse("cart_detail")), 'value="2"')
        self.client.post(
            reverse("cart_update", args=[self.product.pk]), {"quantity": 3}
        )
        response = self.client.get(reverse("order_create"))
        self.assertContains(response, '"quantity": 3')
        response = self.client.post(
            reverse("order_create"),
            {"items": json.dumps([{"product_id": self.product.id, "quantity": 3}])},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("cart"), {})

    def test_delete_is_hard_for_unused_and_safe_for_historical(self):
        unused = product(name="Unused", sku="U-1")
        unused.save()
        self.client.post(reverse("product_delete", args=[unused.pk]))
        self.assertFalse(Product.objects.filter(pk=unused.pk).exists())
        order = Order.objects.create(recommended_box=self.box)
        OrderItem.objects.create(
            order=order, product=self.product, quantity=1, product_snapshot={}
        )
        self.client.post(reverse("product_delete", args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)
        self.client.post(reverse("box_delete", args=[self.box.pk]))
        self.box.refresh_from_db()
        self.assertFalse(self.box.is_active)


class UnitConversionTests(TestCase):
    def test_inch_entry_stores_centimetres_and_displays_inches(self):
        form = ProductForm(
            {
                "name": "Inch product",
                "sku": "IN-1",
                "length": "1",
                "width": "2",
                "height": "3",
                "dimension_unit": "in",
                "weight": "1",
                "is_active": "on",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.length, D("2.54"))
        self.assertEqual(instance.displayed_dimensions, "1.00 × 2.00 × 3.00")

    def test_negative_html_constraints_and_server_validation_remain_active(self):
        form = ProductForm(
            {
                "name": "Bad",
                "sku": "B-1",
                "length": "-1",
                "width": "1",
                "height": "1",
                "dimension_unit": "cm",
                "weight": "1",
                "is_active": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(ProductForm().fields["length"].widget.attrs["min"], "0.01")
