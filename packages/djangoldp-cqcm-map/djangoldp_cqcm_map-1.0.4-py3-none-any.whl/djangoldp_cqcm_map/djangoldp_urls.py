from django.urls import path

from djangoldp_cqcm_map.views import PoleViewset

urlpatterns = (
    path(
        "poles/",
        PoleViewset.urls(),
    ),
)
