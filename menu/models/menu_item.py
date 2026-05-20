from django.db import models


class MenuItem(models.Model):
    class MenuItemType(models.TextChoices):
        VIP = "VIP", "VIP"
        ECO = "ECO", "ECO"

    title = models.CharField(max_length=64)
    category = models.ForeignKey(
        "menu.category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    menu_type = models.CharField(max_length=16, choices=MenuItemType.choices)
    price = models.PositiveIntegerField()
    order_in_category = models.SmallIntegerField()
    show_in_menu = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
