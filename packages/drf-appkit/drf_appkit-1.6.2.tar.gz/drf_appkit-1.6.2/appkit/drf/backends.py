from rest_framework_filters.backends import RestFrameworkFilterBackend


class DRFFilterBackend(RestFrameworkFilterBackend):
    def filter_queryset(self, request, queryset, view):
        qs = super().filter_queryset(request, queryset, view)
        return qs.distinct()