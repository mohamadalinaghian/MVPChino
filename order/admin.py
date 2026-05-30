from django.contrib import admin
from django.utils.html import format_html
from .models import Table, Order, OrderItem


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("name", "open_orders_count")
    search_fields = ("name",)

    @admin.display(description="OPEN Orders")
    def open_orders_count(self, obj):
        """Display count of OPEN orders for this table"""
        count = obj.orders.filter(status=Order.OrderStatus.OPEN).count()
        return format_html(
            '<span style="color: {};">{}</span>',
            "red" if count > 0 else "green",
            count,
        )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("item", "quantity", "unit_price_snapshot", "line_total_display")
    readonly_fields = ("unit_price_snapshot", "line_total_display")

    @admin.display(description="Line Total")
    def line_total_display(self, obj):
        """Display calculated line total"""
        return f"{obj.line_total:,} تومان"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "daily_number",
        "order_target",
        "status_badge",
        "total_price_display",
        "created_at",
    )
    list_filter = ("status", "is_takeaway", "created_at")
    search_fields = ("daily_number", "table__name")
    readonly_fields = (
        "uuid",
        "daily_number",
        "total_price",
        "created_at",
        "items_summary",
    )
    inlines = [OrderItemInline]

    fieldsets = (
        (
            "Order Info",
            {
                "fields": ("uuid", "daily_number", "created_at", "status"),
            },
        ),
        (
            "Target",
            {
                "fields": ("table", "is_takeaway"),
            },
        ),
        (
            "Pricing",
            {
                "fields": ("total_price", "items_summary"),
            },
        ),
    )

    @admin.display(description="Target")
    def order_target(self, obj):
        """Display order target (table or takeaway)"""
        if obj.is_takeaway:
            return format_html('<span style="color: #17a2b8;">🛍️ Takeaway</span>')
        return format_html(
            '<span style="color: #28a745;">🪑 {}</span>',
            obj.table.name if obj.table else "No Table",
        )

    @admin.display(description="status")
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            Order.OrderStatus.OPEN: "#ffc107",
            Order.OrderStatus.PAID: "#28a745",
            Order.OrderStatus.CANCELLED: "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Total")
    def total_price_display(self, obj):
        """Display total price formatted"""
        return f"{obj.total_price:,} تومان"

    @admin.display(description="Items")
    def items_summary(self, obj):
        """Display summary of items in order"""
        items = obj.items.all()
        if not items:
            return "No items"

        lines = [f"<strong>{obj.items.count()} items:</strong><ul>"]
        for item in items:
            lines.append(
                f"<li>{item.item.title} × {item.quantity} = {item.line_total:,} تومان</li>"
            )
        lines.append("</ul>")
        return format_html("".join(lines))


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_display",
        "item",
        "quantity",
        "unit_price_snapshot",
        "line_total",
    )
    list_filter = ("order__created_at", "item__category")
    search_fields = ("order__daily_number", "item__title")
    readonly_fields = ("unit_price_snapshot", "order")

    @admin.display(description="Order")
    def order_display(self, obj):
        """Display order information"""
        return (
            f"Order #{obj.order.daily_number}"
            if obj.order.daily_number
            else str(obj.order.uuid)
        )
