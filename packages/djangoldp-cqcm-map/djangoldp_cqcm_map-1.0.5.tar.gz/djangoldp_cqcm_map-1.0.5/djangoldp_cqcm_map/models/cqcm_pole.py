from django.db import models
from django.utils.translation import gettext_lazy as _
from djangoldp.permissions import ReadAndCreate

from djangoldp_cqcm_map.models.__base import baseNamedModel
from djangoldp_cqcm_map.models.cqcm_location import Location
from djangoldp_cqcm_map.models.cqcm_service import Service
from djangoldp_cqcm_map.models.cqcm_social_network import SocialNetwork
from djangoldp_cqcm_map.models.cqcm_structure_kind import StructureKind


class Pole(baseNamedModel):
    creator_name = models.CharField(max_length=100, blank=True, null=True)
    creator_mail = models.EmailField(blank=True, null=True)
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, blank=True, null=True
    )
    structure_kind = models.ForeignKey(
        StructureKind, on_delete=models.SET_NULL, blank=True, null=True
    )
    services = models.ManyToManyField(Service, blank=True)
    social_networks = models.ManyToManyField(SocialNetwork, blank=True)
    published = models.BooleanField(default=False)

    class Meta(baseNamedModel.Meta):
        verbose_name = _("Pole")
        verbose_name_plural = _("Poles")
        depth = 1

        serializer_fields = baseNamedModel.Meta.serializer_fields + [
            "creator_name",
            "creator_mail",
            "location",
            "structure_kind",
            "services",
            "social_networks",
        ]
        nested_fields = ["location", "structure_kind", "services", "social_networks"]
        rdf_type = "cqcm:Pole"
        permission_classes = [ReadAndCreate]
