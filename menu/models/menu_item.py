from django.db import models
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel


class MenuItem(OrderedModel):
    class MenuItemType(models.TextChoices):
        VIP = "VIP", _("VIP")
        ECO = "ECO", _("ECO")

    title = models.CharField(max_length=64, verbose_name=_("Title"))
    category = models.ForeignKey(
        "menu.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name=_("Category"),
    )
    menu_type = models.CharField(
        max_length=16, choices=MenuItemType.choices, verbose_name=_("Menu Type")
    )
    price = models.PositiveIntegerField(verbose_name=_("Price"))
    show_in_menu = models.BooleanField(
        default=False, db_index=True, verbose_name=_("Show in Menu")
    )
    is_active = models.BooleanField(
        default=True, db_index=True, verbose_name=_("Is Active")
    )
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))

    order_with_respect_to = "category"

    class Meta(OrderedModel.Meta):
        verbose_name = _("Menu Item")
        verbose_name_plural = _("Menu Items")

    def __str__(self):
        return f"{self.title} ({self.get_menu_type_display()})"
