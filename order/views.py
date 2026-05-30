from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Prefetch

from menu.models import Category, MenuItem
from .models import Order, OrderItem, Table


@require_http_methods(["GET"])
def pos_dashboard(request):
    """
    Main POS dashboard.
    Loads all tables, categories, menu items, and the current active order (if any).
    """
    # Get all active tables
    tables = Table.objects.all().order_by("name")
    
    # Get all active categories with their items (prefetch for performance)
    categories = Category.objects.filter(
        is_active=True
    ).prefetch_related(
        Prefetch(
            "items",
            queryset=MenuItem.objects.filter(
                show_in_menu=True,
                is_active=True
            ).order_by("order")
        )
    ).order_by("order")
    
    # Try to get the current active order from session
    current_order = None
    current_order_id = request.session.get("current_order_id")
    
    if current_order_id:
        try:
            current_order = Order.objects.prefetch_related("items__item").get(
                uuid=current_order_id,
                status=Order.OrderStatus.OPEN
            )
        except Order.DoesNotExist:
            # Clear invalid session
            request.session.pop("current_order_id", None)
    
    context = {
        "tables": tables,
        "categories": categories,
        "current_order": current_order,
    }
    
    return render(request, "pos/pos_dashboard.html", context)


@require_http_methods(["POST"])
def select_order_target(request):
    """
    Handle table or takeaway selection.
    If table: Check for existing OPEN order, or create new one.
    If takeaway: Create new OPEN order with is_takeaway=True.
    """
    table_id = request.POST.get("table_id")
    is_takeaway = request.POST.get("is_takeaway") == "true"
    
    # Validate input
    if not table_id and not is_takeaway:
        return HttpResponseBadRequest("Invalid request: specify table_id or is_takeaway")
    
    try:
        if is_takeaway:
            # Create new takeaway order
            order = Order.objects.create(
                is_takeaway=True,
                table=None,
                status=Order.OrderStatus.OPEN
            )
            order.daily_number = order.get_next_daily_number()
            order.save(update_fields=["daily_number"])
        else:
            # Get table
            table = get_object_or_404(Table, id=table_id)
            
            # Check for existing OPEN order on this table
            order = Order.objects.filter(
                table=table,
                status=Order.OrderStatus.OPEN
            ).first()
            
            if not order:
                # Create new order
                order = Order.objects.create(
                    table=table,
                    is_takeaway=False,
                    status=Order.OrderStatus.OPEN
                )
                order.daily_number = order.get_next_daily_number()
                order.save(update_fields=["daily_number"])
        
        # Store current order in session
        request.session["current_order_id"] = str(order.uuid)
        request.session.modified = True
        
        # Return updated order summary (HTMX swap)
        context = {
            "order": order.items.all(),
            "current_order": order,
        }
        return render(request, "pos/order_summary.html", context)
    
    except Exception as e:
        return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["POST"])
def add_item_to_order(request):
    """
    Add a menu item to the current order.
    If item already exists, increment quantity. Otherwise, create new OrderItem.
    """
    menu_item_id = request.POST.get("menu_item_id")
    current_order_id = request.session.get("current_order_id")
    
    # Validate
    if not current_order_id or not menu_item_id:
        return HttpResponseBadRequest("No active order or invalid menu item")
    
    try:
        # Get current order
        order = Order.objects.get(uuid=current_order_id, status=Order.OrderStatus.OPEN)
        
        # Get menu item
        menu_item = get_object_or_404(MenuItem, id=menu_item_id, show_in_menu=True, is_active=True)
        
        # Check if item already in order
        order_item = OrderItem.objects.filter(order=order, item=menu_item).first()
        
        if order_item:
            # Increment quantity
            order_item.quantity += 1
            order_item.save(update_fields=["quantity"])
        else:
            # Create new order item with price snapshot
            OrderItem.objects.create(
                order=order,
                item=menu_item,
                unit_price_snapshot=menu_item.price,
                quantity=1
            )
        
        # Recalculate total
        order.recalculate_total()
        
        # Return updated order summary
        context = {
            "order": order.items.all(),
            "current_order": order,
        }
        return render(request, "pos/order_summary.html", context)
    
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Order not found or not active")
    except Exception as e:
        return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["POST"])
def adjust_item_quantity(request):
    """
    Adjust quantity of an order item.
    If quantity becomes 0, delete the OrderItem entirely.
    """
    order_item_id = request.POST.get("order_item_id")
    action = request.POST.get("action")  # "increment" or "decrement"
    current_order_id = request.session.get("current_order_id")
    
    # Validate
    if not order_item_id or action not in ["increment", "decrement"]:
        return HttpResponseBadRequest("Invalid request")
    
    try:
        # Get order item
        order_item = get_object_or_404(OrderItem, id=order_item_id)
        
        # Verify order is OPEN and matches session
        if str(order_item.order.uuid) != current_order_id or order_item.order.status != Order.OrderStatus.OPEN:
            return HttpResponseBadRequest("Order not active or session mismatch")
        
        order = order_item.order
        
        if action == "increment":
            order_item.quantity += 1
            order_item.save(update_fields=["quantity"])
        elif action == "decrement":
            order_item.quantity -= 1
            
            if order_item.quantity <= 0:
                order_item.delete()
            else:
                order_item.save(update_fields=["quantity"])
        
        # Recalculate total
        order.recalculate_total()
        
        # Return updated order summary
        context = {
            "order": order.items.all(),
            "current_order": order,
        }
        return render(request, "pos/order_summary.html", context)
    
    except OrderItem.DoesNotExist:
        return HttpResponseBadRequest("Order item not found")
    except Exception as e:
        return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["POST"])
def checkout_order(request):
    """
    Checkout and mark order as PAID.
    Render receipt and trigger print.
    """
    current_order_id = request.session.get("current_order_id")
    
    if not current_order_id:
        return HttpResponseBadRequest("No active order")
    
    try:
        order = Order.objects.prefetch_related("items__item").get(
            uuid=current_order_id,
            status=Order.OrderStatus.OPEN
        )
        
        # Mark as PAID
        order.status = Order.OrderStatus.PAID
        order.save(update_fields=["status"])
        
        # Clear session
        request.session.pop("current_order_id", None)
        request.session.modified = True
        
        # Render receipt
        context = {
            "order": order,
            "order_items": order.items.all(),
        }
        return render(request, "pos/receipt.html", context)
    
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Order not found or not active")
    except Exception as e:
        return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["POST"])
def cancel_order(request):
    """
    Cancel an order (mark as CANCELLED).
    """
    current_order_id = request.session.get("current_order_id")
    
    if not current_order_id:
        return HttpResponseBadRequest("No active order")
    
    try:
        order = Order.objects.get(uuid=current_order_id, status=Order.OrderStatus.OPEN)
        
        # Mark as CANCELLED
        order.status = Order.OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        
        # Clear session
        request.session.pop("current_order_id", None)
        request.session.modified = True
        
        # Return empty order state
        return render(request, "pos/empty_order.html")
    
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Order not found")
    except Exception as e:
        return HttpResponseBadRequest(f"Error: {str(e)}")