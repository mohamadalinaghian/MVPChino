from django.db import models


class OrderItem(models.Model):
    order = models.ForeignKey("order.Order", on_delete=models.CASCADE)
    item = models.ForeignKey(
        "menu.MenuItem", on_delete=models.SET_NULL, null=True, blank=True
    )
    unit_price_snapshot = models.PositiveIntegerField()
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    @property
    def line_total(self):
        return self.quantity * self.unit_price_snapshot
