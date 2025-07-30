from djangoldp.views.ldp_viewset import LDPViewSet

from djangoldp_cqcm_map.models.cqcm_pole import Pole


class PoleViewset(LDPViewSet):
    model = Pole

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(published=True)
