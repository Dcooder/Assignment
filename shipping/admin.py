from django.contrib import admin

from .models import Box, Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "weight", "is_active", "updated_at")
    search_fields = ("name", "sku")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "length",
        "width",
        "height",
        "max_weight",
        "shipping_cost",
        "is_active",
    )
    search_fields = ("code",)
    list_filter = ("is_active",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_snapshot",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "created_at",
        "total_weight",
        "recommended_box",
        "status",
    )
    search_fields = ("identifier",)
    list_filter = ("status",)
    readonly_fields = (
        "identifier",
        "created_at",
        "updated_at",
        "total_weight",
        "evaluation",
        "recommended_box_snapshot",
    )
    inlines = [OrderItemInline]
