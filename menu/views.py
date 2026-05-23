from django.shortcuts import render, Http404
from django.db.models import Prefetch
from .models import Category, MenuItem


def landing_page_view(request):
    """
    Renders the landing page where users choose between VIP and ECO menus.
    """
    return render(request, "menu/landing.html")


def menu_list_view(request, menu_type):
    """
    Renders the menu items filtered by category and the requested menu_type.
    """
    # Validate the menu_type parameter (must be VIP or ECO)
    valid_menu_types = ["VIP", "ECO"]
    menu_type_upper = menu_type.upper()

    if menu_type_upper not in valid_menu_types:
        raise Http404("Menu type not found.")

    # Prefetch only active and visible items that match the selected menu_type
    items_prefetch = Prefetch(
        "items",
        queryset=MenuItem.objects.filter(
            is_active=True, show_in_menu=True, menu_type=menu_type_upper
        ).order_by("order"),
    )

    # Fetch active categories and attach the prefetched filtered items (Only 2 DB queries)
    categories = (
        Category.objects.filter(is_active=True)
        .prefetch_related(items_prefetch)
        .order_by("order")
    )

    context = {
        "categories": categories,
        "current_menu_type": menu_type_upper,
    }
    return render(request, "menu/menu_list.html", context)
