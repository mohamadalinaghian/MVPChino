from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=64)
    order = models.SmallIntegerField()
    description = models.CharField(max_length=256, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
