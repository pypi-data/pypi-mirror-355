from rest_framework.filters import BaseFilterBackend

class ValidatedThematicFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.exclude(id=view.kwargs['id'])

class ValidatedDocumenttypeFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.exclude(id=view.kwargs['id'])
