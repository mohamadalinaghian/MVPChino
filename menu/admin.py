from django.contrib import admin
from .models import Category, MenuItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Fields to display in the category list
    list_display = ("title", "order", "is_active")
    
    # Quick edit for order and active status without entering the detail page
    list_editable = ("order", "is_active")
    
    # Search by category title
    search_fields = ("title",)
    
    # Default ordering by order field
    ordering = ("order",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    # Display key information for each item at a glance
    list_display = (
        "title", 
        "category", 
        "price", 
        "menu_type", 
        "show_in_menu", 
        "is_active", 
        "order_in_category"
    )
    
    # Quick edit for price, visibility, status, and order (highly useful for cafe managers)
    list_editable = (
        "price", 
        "show_in_menu", 
        "is_active", 
        "order_in_category"
    )
    
    # Practical filters in the right sidebar
    list_filter = ("category", "menu_type", "show_in_menu", "is_active")
    
    # Search by item title
    search_fields = ("title",)
    
    # Ordering: first by category, then by order within the category
    ordering = ("category", "order_in_category")
    
    # Optimize database queries for foreign keys (prevent N+1 problem)
    list_select_related = ("category",)
