from django.db import models
from django.utils.translation import gettext_lazy as _

from djangoldp_cqcm_map.models.__base import baseNamedModel
from djangoldp_cqcm_map.models.cqcm_location import Location
from djangoldp_cqcm_map.models.cqcm_service import Service
from djangoldp_cqcm_map.models.cqcm_social_network import SocialNetwork
from djangoldp_cqcm_map.models.cqcm_structure_kind import StructureKind


class Pole(baseNamedModel):
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, blank=True, null=True
    )
    structure_kind = models.ForeignKey(
        StructureKind, on_delete=models.SET_NULL, blank=True, null=True
    )
    services = models.ManyToManyField(Service, blank=True)
    social_networks = models.ManyToManyField(SocialNetwork, blank=True)

    class Meta(baseNamedModel.Meta):
        verbose_name = _("Pole")
        verbose_name_plural = _("Poles")
        depth = 1

        serializer_fields = baseNamedModel.Meta.serializer_fields + [
            "location",
            "structure_kind",
            "services",
            "social_networks",
        ]
        nested_fields = ["location", "structure_kind", "services", "social_networks"]
        rdf_type = "cqcm:Pole"
