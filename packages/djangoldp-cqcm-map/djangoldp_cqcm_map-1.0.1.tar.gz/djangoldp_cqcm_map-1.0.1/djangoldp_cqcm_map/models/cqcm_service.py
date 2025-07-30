from django.utils.translation import gettext_lazy as _

from djangoldp_cqcm_map.models.__base import baseNamedModel


class Service(baseNamedModel):

    class Meta(baseNamedModel.Meta):
        verbose_name = _("Service")
        verbose_name_plural = _("Services")

        serializer_fields = baseNamedModel.Meta.serializer_fields
        rdf_type = "cqcm:Service"
