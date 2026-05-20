from django.db import models
import uuid


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.PositiveBigIntegerField()
    status = models.CharField(
        max_length=32, choices=OrderStatus.choices, default=OrderStatus.OPEN
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
