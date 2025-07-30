from django.contrib import admin
from djangoldp.admin import DjangoLDPAdmin

from djangoldp_cqcm_map.models import *


class CQCMMapModelAdmin(DjangoLDPAdmin):
    readonly_fields = (
        "urlid",
        "creation_date",
        "update_date",
    )
    list_filter = (
        "creation_date",
        "update_date",
    )
    exclude = ("is_backlink", "allow_create_backlink")
    extra = 0


@admin.register(Pole)
class PoleAdmin(CQCMMapModelAdmin):
    list_display = (
        "urlid",
        "name",
        "location",
        "structure_kind",
        "creation_date",
        "update_date",
    )
    search_fields = [
        "name",
        "location__address",
        "structure_kind__name",
        "services__name",
    ]
    list_filter = tuple(CQCMMapModelAdmin.list_filter) + (
        "structure_kind",
        "services",
    )
    ordering = ["name"]


@admin.register(Location)
class LocationAdmin(CQCMMapModelAdmin):
    list_display = (
        "urlid",
        "address",
        "lat",
        "lng",
        "creation_date",
        "update_date",
    )
    search_fields = [
        "address",
    ]
    ordering = ["address"]


@admin.register(
    StructureKind,
    Service,
)
class StructureKindAdmin(CQCMMapModelAdmin):
    list_display = (
        "urlid",
        "name",
        "creation_date",
        "update_date",
    )
    search_fields = [
        "name",
    ]
    ordering = ["name"]


@admin.register(SocialNetwork)
class SocialNetworkAdmin(CQCMMapModelAdmin):
    list_display = (
        "urlid",
        "url",
        "kind",
        "creation_date",
        "update_date",
    )
    search_fields = [
        "url",
        "kind",
    ]
    list_filter = tuple(CQCMMapModelAdmin.list_filter) + ("kind",)
    ordering = ["kind", "url"]
