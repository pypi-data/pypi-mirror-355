from django.db import models
from django.utils.translation import gettext_lazy as _

from djangoldp_cqcm_map.models.__base import baseModel

VALID_KINDS = [
    ("twitter", _("Twitter")),
    ("facebook", _("Facebook")),
    ("instagram", _("Instagram")),
    ("youtube", _("Youtube")),
    ("linkedin", _("Linkedin")),
    ("link", _("Link")),
    ("mail", _("Mail")),
]


class SocialNetwork(baseModel):
    url = models.CharField(max_length=3000, blank=True, null=True)
    kind = models.CharField(max_length=20, choices=VALID_KINDS, blank=True, null=True, default="link")

    def __str__(self):
        return self.url

    class Meta(baseModel.Meta):
        verbose_name = _("Social Network")
        verbose_name_plural = _("Social Networks")

        serializer_fields = baseModel.Meta.serializer_fields + [
            "url",
            "kind",
        ]
        rdf_type = "cqcm:SocialNetwork"
