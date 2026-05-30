from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Prefetch
from django.utils import timezone

from menu.models import MenuItem, Category
from .models import Order, Table, OrderItem


# ============================================================================
# MAIN POS DASHBOARD
# ============================================================================

def pos_dashboard_view(request):
    """
    Main POS dashboard: renders left panel (empty initially) + right panel
    with tables, categories, and menu items.
    """
    # Fetch all active tables
    tables = Table.objects.all().order_by("name")
    
    # Prefetch active menu items for each active category
    items_prefetch = Prefetch(
        "items",
        queryset=MenuItem.objects.filter(
            is_active=True, show_in_menu=True
        ).order_by("order"),
    )
    
    categories = (
        Category.objects.filter(is_active=True)
        .prefetch_related(items_prefetch)
        .order_by("order")
    )
    
    context = {
        "tables": tables,
        "categories": categories,
        "current_order": None,  # No active order initially
    }
    
    return render(request, "order/pos_dashboard.html", context)


# ============================================================================
# ORDER TARGET SELECTION (Table or Takeaway)
# ============================================================================

@require_http_methods(["POST"])
def select_order_target(request):
    """
    HTMX endpoint: Select a table or create a takeaway order.
    
    POST params:
    - table_id: (optional) Table UUID/ID to select
    - is_takeaway: (optional) "true" to create takeaway order
    
    Returns: Updated order summary partial (left panel)
    """
    table_id = request.POST.get("table_id")
    is_takeaway = request.POST.get("is_takeaway") == "true"
    
    current_order = None
    
    if is_takeaway:
        # Create new OPEN takeaway order
        current_order = Order.objects.create(
            is_takeaway=True,
            table=None,
            status=Order.OrderStatus.OPEN,
        )
        current_order.daily_number = current_order.get_next_daily_number()
        current_order.save(update_fields=["daily_number"])
    
    elif table_id:
        # Try to load OPEN order for this table
        table = get_object_or_404(Table, id=table_id)
        current_order = Order.objects.filter(
            table=table, status=Order.OrderStatus.OPEN
        ).first()
        
        # If no OPEN order exists, create one
        if not current_order:
            current_order = Order.objects.create(
                table=table,
                status=Order.OrderStatus.OPEN,
            )
            current_order.daily_number = current_order.get_next_daily_number()
            current_order.save(update_fields=["daily_number"])
    
    else:
        # No valid target provided
        return HttpResponseBadRequest("table_id or is_takeaway required")
    
    # Return updated order summary partial
    return render(
        request,
        "order/partials/order_summary.html",
        {"current_order": current_order}
    )


# ============================================================================
# ADD ITEM TO ORDER
# ============================================================================

@require_http_methods(["POST"])
def add_item_to_order(request, uuid):
    """
    HTMX endpoint: Add menu item to active order.
    
    POST params:
    - menu_item_id: MenuItem ID to add
    - quantity: (optional, default=1) Quantity to add
    
    Returns: Updated order summary partial
    """
    current_order = get_object_or_404(Order, uuid=uuid)
    
    # Validate order is OPEN
    if current_order.status != Order.OrderStatus.OPEN:
        return HttpResponseForbidden("Order is not OPEN. Cannot add items.")
    
    menu_item_id = request.POST.get("menu_item_id")
    quantity = int(request.POST.get("quantity", 1))
    
    if not menu_item_id or quantity < 1:
        return HttpResponseBadRequest("Invalid menu_item_id or quantity")
    
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    # Check if OrderItem already exists for this menu item
    order_item = OrderItem.objects.filter(
        order=current_order, item=menu_item
    ).first()
    
    if order_item:
        # Increase quantity
        order_item.quantity += quantity
        order_item.save(update_fields=["quantity"])
    else:
        # Create new OrderItem with snapshot of current price
        OrderItem.objects.create(
            order=current_order,
            item=menu_item,
            unit_price_snapshot=menu_item.price,
            quantity=quantity,
        )
    
    # Recalculate total
    current_order.recalculate_total()
    
    # Return updated order summary
    return render(
        request,
        "order/partials/order_summary.html",
        {"current_order": current_order}
    )


# ============================================================================
# UPDATE ITEM QUANTITY (Increment/Decrement)
# ============================================================================

@require_http_methods(["POST"])
def update_item_quantity(request, uuid):
    """
    HTMX endpoint: Update quantity of an item in the order (±).
    
    POST params:
    - order_item_id: OrderItem ID to modify
    - action: "increment" or "decrement"
    
    Returns: Updated order summary partial
    """
    current_order = get_object_or_404(Order, uuid=uuid)
    
    # Validate order is OPEN
    if current_order.status != Order.OrderStatus.OPEN:
        return HttpResponseForbidden("Order is not OPEN. Cannot modify items.")
    
    order_item_id = request.POST.get("order_item_id")
    action = request.POST.get("action")
    
    if not order_item_id or action not in ["increment", "decrement"]:
        return HttpResponseBadRequest("Invalid order_item_id or action")
    
    order_item = get_object_or_404(OrderItem, id=order_item_id, order=current_order)
    
    if action == "increment":
        order_item.quantity += 1
        order_item.save(update_fields=["quantity"])
    
    elif action == "decrement":
        if order_item.quantity - 1 == 0:
            # Delete if quantity reaches 0
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save(update_fields=["quantity"])
    
    # Recalculate total
    current_order.recalculate_total()
    
    # Return updated order summary
    return render(
        request,
        "order/partials/order_summary.html",
        {"current_order": current_order}
    )


# ============================================================================
# CHECKOUT & PAYMENT
# ============================================================================

@require_http_methods(["POST"])
def checkout_order(request, uuid):
    """
    Checkout: Change order status from OPEN to PAID and redirect to receipt.
    
    Returns: Redirect to receipt view
    """
    current_order = get_object_or_404(Order, uuid=uuid)
    
    # Validate order is OPEN
    if current_order.status != Order.OrderStatus.OPEN:
        return HttpResponseForbidden("Order is not OPEN. Cannot checkout.")
    
    # Validate order has items
    if not current_order.items.exists():
        return HttpResponseBadRequest("Order has no items. Cannot checkout.")
    
    # Change status to PAID
    current_order.status = Order.OrderStatus.PAID
    current_order.save(update_fields=["status"])
    
    # Redirect to receipt view (which will print automatically)
    return redirect("order:receipt", uuid=uuid)


# ============================================================================
# RECEIPT (Customer Print)
# ============================================================================

def receipt_view(request, uuid):
    """
    Display thermal-printer-friendly receipt for paid order.
    Auto-triggers print dialog via JS.
    """
    current_order = get_object_or_404(Order, uuid=uuid)
    
    # Validate order is PAID
    if current_order.status != Order.OrderStatus.PAID:
        return HttpResponseForbidden("Order must be PAID to view receipt.")
    
    context = {
        "order": current_order,
    }
    
    response = render(request, "order/receipt.html", context)
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# ============================================================================
# KITCHEN PRINT (Bar/Kitchen Ticket)
# ============================================================================

def kitchen_print_view(request, uuid):
    """
    Display kitchen/bar prep ticket for OPEN order.
    Auto-triggers print dialog via JS.
    """
    current_order = get_object_or_404(Order, uuid=uuid)
    
    # Allow printing for OPEN orders only (staff feature during order prep)
    if current_order.status != Order.OrderStatus.OPEN:
        return HttpResponseForbidden("Kitchen ticket only available for OPEN orders.")
    
    context = {
        "order": current_order,
    }
    
    response = render(request, "order/kitchen_ticket.html", context)
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
