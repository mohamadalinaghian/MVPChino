from django.contrib import admin
from .models import Table, Order, OrderItem


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["daily_number", "table", "is_takeaway", "status", "total_price", "created_at"]
    list_filter = ["status", "is_takeaway", "created_at"]
    search_fields = ["daily_number", "table__name"]
    readonly_fields = ["uuid", "created_at", "total_price"]
    fieldsets = (
        ("Order Info", {
            "fields": ("uuid", "daily_number", "table", "is_takeaway", "status")
        }),
        ("Pricing", {
            "fields": ("total_price",)
        }),
        ("Timestamps", {
            "fields": ("created_at",)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing order
            return self.readonly_fields + ["daily_number", "table", "is_takeaway"]
        return self.readonly_fields


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "item", "quantity", "unit_price_snapshot", "line_total"]
    list_filter = ["order__status", "order__created_at"]
    search_fields = ["order__daily_number", "item__title"]
    readonly_fields = ["line_total"]

    def line_total(self, obj):
        return obj.line_total
    line_total.short_description = "Line Total"