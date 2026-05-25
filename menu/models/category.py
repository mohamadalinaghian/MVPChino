from django.db import models
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel


class Category(OrderedModel):
    title = models.CharField(max_length=64, verbose_name=_("Title"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    is_active = models.BooleanField(
        default=True, db_index=True, verbose_name=_("Is Active")
    )

    class Meta(OrderedModel.Meta):
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title
