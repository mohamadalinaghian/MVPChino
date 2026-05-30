import uuid
from django.db import models
from django.utils import timezone
from django.db.models import Sum, F, Max


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
    daily_number = models.PositiveIntegerField(null=True, blank=True)
    is_takeaway = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.PositiveBigIntegerField(default=0)
    status = models.CharField(
        max_length=32, choices=OrderStatus.choices, default=OrderStatus.OPEN
    )

    def __str__(self):
        if self.daily_number:
            return f"Order #{self.daily_number} - {self.table.name if self.table else 'Takeaway'}"
        return f"Order {self.uuid} - {self.table.name if self.table else 'Takeaway'}"

    # helper functions

    def recalculate_total(self):
        # Calculate total price directly from DB
        total = (
            self.items.annotate(
                line=F("quantity") * F("unit_price_snapshot")
            ).aggregate(total_sum=Sum("line"))["total_sum"]
            or 0
        )

        self.total_price = total
        self.save(update_fields=["total_price"])

    def get_next_daily_number(self, date=None):
        """Get the next sequential daily_number for the given date (default: today)"""

        if date is None:
            date = timezone.now().date()

        # Find max daily_number for orders created today
        max_number = Order.objects.filter(created_at__date=date).aggregate(
            Max("daily_number")
        )["daily_number__max"]

        return (max_number or 0) + 1
