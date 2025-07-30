from django.utils.translation import gettext_lazy as _

from djangoldp_cqcm_map.models.__base import baseNamedModel


class StructureKind(baseNamedModel):

    class Meta(baseNamedModel.Meta):
        verbose_name = _("Structure kind")
        verbose_name_plural = _("Structure kinds")

        serializer_fields = baseNamedModel.Meta.serializer_fields
        rdf_type = "cqcm:StructureKind"
