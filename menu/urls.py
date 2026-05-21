from django.urls import path
from . import views

app_name = "menu"

urlpatterns = [
    # Landing page at the root of this app
    path("", views.landing_page_view, name="landing"),
    
    # Dynamic URL for menu types (e.g., /vip/menu/ or /eco/menu/)
    path("<str:menu_type>/menu/", views.menu_list_view, name="menu_list"),
]
