from django.db.models.deletion import RestrictedError, ProtectedError
from rest_framework.status import (
    HTTP_204_NO_CONTENT,
    HTTP_423_LOCKED
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings


class DestroyModelMixin(object):
    """
    Override of DRF implementation in rest_framework/mixins.
    In the event that a record can not be deleted due to a protected foreign key,
    it is preferable to construct a standard error response rather than
    simply bomb with a django exception.
    See: https://github.com/encode/django-rest-framework/issues/5958
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except (RestrictedError, ProtectedError) as e:
            if hasattr(self, 'get_info_for_exception'):
                error_info = self.get_info_for_exception(e)
            else:
                error_info = {'detail': str(e)}

            return Response(status=HTTP_423_LOCKED, data=error_info)
        return Response(status=HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class DynamicSerializerMixin(object):
    def get_serializer_class(self):
        if not self.serializers:
            return super().get_serializer_class()

        action_name = self.action

        serializer_access_method_name = 'get_{}_serializer_class'.format(action_name)
        if hasattr(self, serializer_access_method_name):
            return getattr(self, serializer_access_method_name)()

        if action_name in self.serializers:
            return self.serializers[action_name]

        detail_serializer = self.serializers.get('retrieve')
        if detail_serializer and action_name in self.get_detail_actions():
            return detail_serializer

        edit_serializer = self.serializers.get('update')
        if edit_serializer and action_name in self.get_edit_actions():
            return edit_serializer

        return self.serializers['default']


class ListExportMixin(object):
    @action(detail=False, methods=['get'])
    def export(self, request):
        item_qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(item_qs, many=True)
        return Response(serializer.data)


class PaginationMixin(object):
    def pagination_class(self):
        pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
        if pagination_class is None:
            return None

        disable_paging = self.request.query_params.get('disable_paging', False)
        if disable_paging == 'true':
            return None

        return api_settings.DEFAULT_PAGINATION_CLASS()
