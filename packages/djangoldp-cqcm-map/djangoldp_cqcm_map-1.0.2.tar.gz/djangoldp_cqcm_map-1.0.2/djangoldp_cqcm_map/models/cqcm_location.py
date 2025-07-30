from django.db import models
from django.utils.translation import gettext_lazy as _

from djangoldp_cqcm_map.models.__base import baseModel


class Location(baseModel):
    address = models.TextField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.address

    class Meta(baseModel.Meta):
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

        serializer_fields = baseModel.Meta.serializer_fields + [
            "lat",
            "lng",
            "address",
        ]
        rdf_type = "cqcm:Location"
