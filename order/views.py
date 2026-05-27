from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import Order, OrderItem, OrderStatus, Table
from menu.models import Category, MenuItem

def pos_dashboard(request):
    categories = Category.objects.filter(is_active=True).prefetch_related('menuitem_set')
    tables = Table.objects.all()
    open_orders = Order.objects.filter(status=OrderStatus.OPEN).order_by('-created_at')
    
    # Get active order from session
    current_order_id = request.session.get('current_order_id')
    current_order = None
    if current_order_id:
        current_order = Order.objects.filter(uuid=current_order_id, status=OrderStatus.OPEN).first()
        # If it was paid/deleted in another window, clear session
        if not current_order:
            del request.session['current_order_id']

    context = {
        'categories': categories,
        'tables': tables,
        'open_orders': open_orders,
        'order': current_order,
    }
    return render(request, 'order/pos_dashboard.html', context)

@require_POST
def start_new_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    order = Order.objects.create(table=table, status=OrderStatus.OPEN)
    request.session['current_order_id'] = str(order.uuid)
    
    response = HttpResponse()
    response['HX-Redirect'] = reverse('order:pos_dashboard')
    return response

@require_POST
def switch_order(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid, status=OrderStatus.OPEN)
    request.session['current_order_id'] = str(order.uuid)
    
    response = HttpResponse()
    response['HX-Redirect'] = reverse('order:pos_dashboard')
    return response

@require_POST
def save_order(request):
    if 'current_order_id' in request.session:
        del request.session['current_order_id']
        
    response = HttpResponse()
    response['HX-Redirect'] = reverse('order:pos_dashboard')
    return response

@require_POST
def checkout_order(request):
    current_order_id = request.session.get('current_order_id')
    if current_order_id:
        order = Order.objects.filter(uuid=current_order_id, status=OrderStatus.OPEN).first()
        if order:
            order.status = OrderStatus.PAID
            order.save()
        del request.session['current_order_id']
        
    response = HttpResponse()
    response['HX-Redirect'] = reverse('order:pos_dashboard')
    return response

@require_POST
def add_to_cart(request, item_id):
    current_order_id = request.session.get('current_order_id')
    if not current_order_id:
        return HttpResponse("<div class='cart-empty'>لطفا ابتدا یک میز یا سفارش باز انتخاب کنید.</div>")
        
    order = get_object_or_404(Order, uuid=current_order_id, status=OrderStatus.OPEN)
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    order_item, created = OrderItem.objects.get_or_create(
        order=order,
        menu_item=menu_item,
        defaults={'unit_price_snapshot': menu_item.price, 'quantity': 1}
    )
    if not created:
        order_item.quantity += 1
        order_item.save()

    # Recalculate Total
    order.total_price = sum(item.line_total for item in order.orderitem_set.all())
    order.save()

    return render(request, 'order/partials/cart.html', {'order': order})

@require_POST
def decrease_quantity(request, item_id):
    current_order_id = request.session.get('current_order_id')
    if not current_order_id:
        return HttpResponse("<div class='cart-empty'>سفارش یافت نشد.</div>")

    order = get_object_or_404(Order, uuid=current_order_id, status=OrderStatus.OPEN)
    order_item = get_object_or_404(OrderItem, order=order, menu_item_id=item_id)

    if order_item.quantity > 1:
        order_item.quantity -= 1
        order_item.save()
    else:
        order_item.delete()

    order.total_price = sum(item.line_total for item in order.orderitem_set.all())
    order.save()

    return render(request, 'order/partials/cart.html', {'order': order})
