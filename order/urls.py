from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('pos/', views.pos_dashboard, name='pos_dashboard'),
    path('pos/cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('pos/cart/decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    
    # New endpoints for Table & Order Management
    path('pos/order/new/<int:table_id>/', views.start_new_order, name='start_new_order'),
    path('pos/order/switch/<uuid:order_uuid>/', views.switch_order, name='switch_order'),
    path('pos/order/save/', views.save_order, name='save_order'),
    path('pos/order/checkout/', views.checkout_order, name='checkout_order'),
]
