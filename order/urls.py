from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    # Main POS Dashboard
    path("pos/", views.pos_dashboard_view, name="pos_dashboard"),
    
    # Order Management (HTMX endpoints)
    path("pos/order/select-target/", views.select_order_target, name="select_order_target"),
    path("pos/order/<uuid:uuid>/add-item/", views.add_item_to_order, name="add_item_to_order"),
    path("pos/order/<uuid:uuid>/update-item/", views.update_item_quantity, name="update_item_quantity"),
    
    # Checkout & Printing
    path("pos/order/<uuid:uuid>/checkout/", views.checkout_order, name="checkout_order"),
    path("pos/order/<uuid:uuid>/receipt/", views.receipt_view, name="receipt"),
    path("pos/order/<uuid:uuid>/kitchen/", views.kitchen_print_view, name="kitchen_print"),
]
