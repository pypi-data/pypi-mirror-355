from django.conf.urls import url
from django.urls import path, include
from djangoldp_blog.views import RelatedThematicsViewset, RelatedDocumentsViewset



urlpatterns = [
    path('tinymce/', include('tinymce.urls')),
    url(r'^thematics/(?P<id>.+)/related/', RelatedThematicsViewset.urls(model_prefix="related-thematics")),
    url(r'^documenttypes/(?P<id>.+)/related/', RelatedDocumentsViewset.urls(model_prefix="related-documents")),
]


