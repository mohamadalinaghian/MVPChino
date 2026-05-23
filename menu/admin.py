# menu/admin.py
from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin
from .models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(OrderedModelAdmin):
    # اضافه کردن فیلد 'move_up_down_links' به لیست نمایش، دکمه‌های جابه‌جایی را به ادمین اضافه می‌کند
    list_display = ("title", "is_active", "move_up_down_links")


@admin.register(MenuItem)
class MenuItemAdmin(OrderedModelAdmin):
    list_display = ("title", "category", "price", "is_active", "move_up_down_links")
    list_filter = ("category", "is_active")
