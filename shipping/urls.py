from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing_or_dashboard, name="dashboard"),
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_form, name="product_create"),
    path("products/<int:pk>/edit/", views.product_form, name="product_edit"),
    path("products/<int:pk>/toggle/", views.product_toggle, name="product_toggle"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("boxes/", views.box_list, name="box_list"),
    path("boxes/new/", views.box_form, name="box_create"),
    path("boxes/<int:pk>/edit/", views.box_form, name="box_edit"),
    path("boxes/<int:pk>/toggle/", views.box_toggle, name="box_toggle"),
    path("boxes/<int:pk>/delete/", views.box_delete, name="box_delete"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/<int:pk>/", views.cart_update, name="cart_update"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/new/", views.order_create, name="order_create"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
]
