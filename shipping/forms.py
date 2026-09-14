from django import forms
from decimal import Decimal
from .models import Box, Product
from .units import from_centimetres, to_centimetres


class DimensionUnitFormMixin:
    dimension_fields = ("length", "width", "height")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.dimension_fields:
            self.fields[name].widget.attrs.update({"min": "0.01", "step": "0.01"})
        for name in ("weight", "max_weight"):
            if name in self.fields:
                self.fields[name].widget.attrs.update({"min": "0.001", "step": "0.001"})
        if "shipping_cost" in self.fields:
            self.fields["shipping_cost"].widget.attrs.update(
                {"min": "0", "step": "0.01"}
            )
        if self.instance and self.instance.pk:
            unit = self.instance.dimension_unit
            for name in self.dimension_fields:
                self.initial[name] = from_centimetres(
                    getattr(self.instance, name), unit
                ).quantize(Decimal("0.01"))

    def clean(self):
        cleaned = super().clean()
        unit = cleaned.get("dimension_unit", "cm")
        for name in self.dimension_fields:
            if cleaned.get(name) is not None:
                cleaned[name] = to_centimetres(cleaned[name], unit).quantize(
                    Decimal("0.01")
                )
        return cleaned


class ProductForm(DimensionUnitFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "length",
            "width",
            "height",
            "dimension_unit",
            "weight",
            "is_active",
        ]


class BoxForm(DimensionUnitFormMixin, forms.ModelForm):
    class Meta:
        model = Box
        fields = [
            "code",
            "length",
            "width",
            "height",
            "dimension_unit",
            "max_weight",
            "shipping_cost",
            "is_active",
        ]


class OrderBuildForm(forms.Form):
    items = forms.CharField(widget=forms.HiddenInput)

    def clean_items(self):
        import json

        try:
            items = json.loads(self.cleaned_data["items"])
        except (ValueError, TypeError):
            raise forms.ValidationError("Order contents are invalid.")
        if not isinstance(items, list) or not items:
            raise forms.ValidationError("Add at least one product.")
        cleaned = {}
        for row in items:
            try:
                product_id, quantity = int(row["product_id"]), int(row["quantity"])
            except (KeyError, TypeError, ValueError):
                raise forms.ValidationError(
                    "Each item needs a valid product and quantity."
                )
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than zero.")
            cleaned[product_id] = cleaned.get(product_id, 0) + quantity
        products = {
            p.id: p for p in Product.objects.filter(id__in=cleaned, is_active=True)
        }
        if len(products) != len(cleaned):
            raise forms.ValidationError(
                "Only active products can be added to a new order."
            )
        return [(products[pid], quantity) for pid, quantity in sorted(cleaned.items())]
