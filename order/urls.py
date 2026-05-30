from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    # POS Dashboard
    path("pos/", views.pos_dashboard, name="pos_dashboard"),
    
    # Order Target Selection (Table or Takeaway)
    path("pos/select-target/", views.select_order_target, name="select_order_target"),
    
    # Item Management
    path("pos/order/add-item/", views.add_item_to_order, name="add_item_to_order"),
    path("pos/order/adjust-quantity/", views.adjust_item_quantity, name="adjust_item_quantity"),
    
    # Checkout
    path("pos/order/checkout/", views.checkout_order, name="checkout_order"),
    
    # Cancel Order
    path("pos/order/cancel/", views.cancel_order, name="cancel_order"),
]