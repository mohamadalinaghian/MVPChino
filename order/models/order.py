import uuid
from django.db import models


class Table(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    table = models.ForeignKey(
        Table, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    order_number = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.PositiveBigIntegerField(default=0)
    status = models.CharField(
        max_length=32, choices=OrderStatus.choices, default=OrderStatus.OPEN
    )

    def __str__(self):
        if self.order_number:
            return f"Order #{self.order_number} - {self.table.name if self.table else 'Takeaway'}"
        return f"Order {self.uuid} - {self.table.name if self.table else 'Takeaway'}"
