from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("menu.urls")),   # Removed name="menu"
    path("", include("order.urls")),  # Removed name="order"
]
