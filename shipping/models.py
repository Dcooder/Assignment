from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from .units import DIMENSION_UNITS, format_dimensions


class DimensionValidationMixin(models.Model):
    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        for field in ("length", "width", "height"):
            if getattr(self, field, None) is not None and getattr(self, field) <= 0:
                raise ValidationError({field: "Must be greater than zero."})


class Product(DimensionValidationMixin):
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=64, unique=True)
    length = models.DecimalField(max_digits=8, decimal_places=2)
    width = models.DecimalField(max_digits=8, decimal_places=2)
    height = models.DecimalField(max_digits=8, decimal_places=2)
    weight = models.DecimalField(max_digits=8, decimal_places=3)
    dimension_unit = models.CharField(
        max_length=2, choices=DIMENSION_UNITS, default="cm"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "sku"]

    def clean(self):
        super().clean()
        if not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank."})
        if self.weight is not None and self.weight <= 0:
            raise ValidationError({"weight": "Must be greater than zero."})

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def displayed_dimensions(self):
        return format_dimensions(
            (self.length, self.width, self.height), self.dimension_unit
        )


class Box(DimensionValidationMixin):
    code = models.CharField(max_length=64, unique=True)
    length = models.DecimalField("internal length", max_digits=8, decimal_places=2)
    width = models.DecimalField("internal width", max_digits=8, decimal_places=2)
    height = models.DecimalField("internal height", max_digits=8, decimal_places=2)
    max_weight = models.DecimalField(max_digits=8, decimal_places=3)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    dimension_unit = models.CharField(
        max_length=2, choices=DIMENSION_UNITS, default="cm"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["shipping_cost", "code"]

    def clean(self):
        super().clean()
        if self.max_weight is not None and self.max_weight <= 0:
            raise ValidationError({"max_weight": "Must be greater than zero."})
        if self.shipping_cost is not None and self.shipping_cost < 0:
            raise ValidationError({"shipping_cost": "Cannot be negative."})

    def __str__(self):
        return self.code

    @property
    def displayed_dimensions(self):
        return format_dimensions(
            (self.length, self.width, self.height), self.dimension_unit
        )


class Order(models.Model):
    class Status(models.TextChoices):
        RECOMMENDED = "recommended", "Recommended"
        NO_SOLUTION = "no_solution", "No suitable box"

    identifier = models.CharField(max_length=24, unique=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    total_weight = models.DecimalField(
        max_digits=10, decimal_places=3, default=Decimal("0")
    )
    recommended_box = models.ForeignKey(
        Box,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recommended_orders",
    )
    recommended_box_snapshot = models.JSONField(default=dict, blank=True)
    selected_box_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NO_SOLUTION
    )
    evaluation = models.JSONField(default=list, blank=True)
    packing_result = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.identifier:
            self.identifier = (
                f"ORD-{timezone.now():%Y%m%d}-{(Order.objects.count() + 1):04d}"
            )
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return self.identifier


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, null=True, blank=True, on_delete=models.SET_NULL
    )
    quantity = models.PositiveIntegerField()
    product_snapshot = models.JSONField(default=dict)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Must be greater than zero."})

    def __str__(self):
        return f"{self.quantity} × {self.product_snapshot.get('name', self.product)}"
