from djangoldp.filters import LocalObjectFilterBackend
from djangoldp.views.ldp_viewset import LDPViewSet
from djangoldp_blog.models import Thematic, Documenttype
from djangoldp_blog.filters import ValidatedThematicFilterBackend, ValidatedDocumenttypeFilterBackend

class RelatedThematicsViewset(LDPViewSet):
    model = Thematic
    filter_backends = [ValidatedThematicFilterBackend, LocalObjectFilterBackend]


class RelatedDocumentsViewset(LDPViewSet):
    model = Documenttype
    filter_backends = [ValidatedDocumenttypeFilterBackend, LocalObjectFilterBackend]
