from django.contrib.auth.models import Group
from django.core.exceptions import FieldError
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import exceptions, viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import (
    # OrderingFilter as DRFOrderingFilter,
    SearchFilter as DRFSearchFilter,
)
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)
from rest_framework_simplejwt.views import TokenViewBase

from djoser.views import UserViewSet as DjoserUserViewSet

from ..auth import get_userprofile_model

from ..models import (
    Attachment,
    MediaAttachment,
    Note,
    Place,
    Region,
    Tag,
)
from ..drf.filters import (
    FilterSet,
    MasterDetailViewFilterBackend,
    # SearchFilter,
)
from ..drf.endpoints import DRFAutoEndpoint
from ..drf.mixins import (
    DestroyModelMixin,
    DynamicSerializerMixin,
    PaginationMixin,
)

from ..util import (
    filter_dict,
    primitive_attribute_names,
)

from . import mixins
from . import serializers
from . import filters

UserProfile = get_userprofile_model()

# ------------------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------------------
class TokenObtainPairView(TokenViewBase):
    """
    Overridden to add additional enforcement over who can access the admin
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.serializer_class = kwargs.get(
            'serializer_class', TokenObtainPairSerializer
        )

    def get_serializer_class(self):
        return self.serializer_class


class UserViewSet(DjoserUserViewSet):
    filterset_class = filters.UserFilter
    serializer_class = serializers.UserListSerializer

    def perform_update(self, serializer):
        """
        Overridden to circumvent sending of activation
        email in response to _any_ update action.
        """
        serializer.save()

    @action(["patch"], detail=False)
    def force_password(self, request, *args, **kwargs):
        serializer = serializers.ForcePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']

        user.set_password(new_password)
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = serializers.PlaceSerializer


class RegionViewSet(PaginationMixin, viewsets.ModelViewSet):
    filterset_class = filters.RegionFilter
    ordering = 'name'
    queryset = Region.objects.all()
    search_fields = ('name',)
    serializer_class = serializers.RegionSerializer


class TagViewSet(PaginationMixin, viewsets.ModelViewSet):
    filterset_class = filters.TagFilter
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class MasterDetailViewSet(
    DestroyModelMixin,
    DynamicSerializerMixin,
    PaginationMixin,
    viewsets.ModelViewSet):
    """
    Base class to provide defaults and behavior
    that is common across all ModelViewSets
    """
    allow_duplicate_records = False

    edit_actions = ('create', 'partial_update', 'update',)
    detail_actions = ('retrieve',)
    serializers = None
    filterset_class = FilterSet
    search_filter_class = DRFSearchFilter

    @property
    def endpoint(self):
        return DRFAutoEndpoint(self.queryset.model, viewset=self)

    @property
    def filter_backends(self):
        backends = [MasterDetailViewFilterBackend] + api_settings.DEFAULT_FILTER_BACKENDS

        search_param_name = api_settings.SEARCH_PARAM
        if self.request.query_params.get(search_param_name, ''):
            backends.append(self.get_search_filter_class())

        return backends

    def get_search_filter_class(self):
        return self.search_filter_class

    def get_metadata_serializer_class(self):
        if not self.serializers:
            return super().get_serializer_class()

        action = self.request.query_params.get('action')
        if action in self.serializers:
            return self.serializers[action]

        return self.serializers['default']

    def get_metadata_fielddict_class(self):
        assert self.metadata_fielddict_class is not None, (
            "'%s' should either include a `metadata_fielddict_class` attribute, "
            "or override the `get_metadata_fielddict_class()` method."
            % self.__class__.__name__
        )
        return self.metadata_fielddict_class

    def get_detail_actions(self):
        assert self.detail_actions is not None, (
            "'%s' should either include a `detail_actions` attribute, "
            "or override the `get_detail_actions()` method."
            % self.__class__.__name__
        )
        return self.detail_actions

    def get_edit_actions(self):
        assert self.edit_actions is not None, (
            "'%s' should either include a `get_edit_actions` attribute, "
            "or override the `get_edit_actions()` method."
            % self.__class__.__name__
        )
        return self.edit_actions

    def get_filterset_class(self):
        assert self.filterset_class is not None, (
            "'%s' should either include a `filterset_class` attribute, "
            "or override the `get_filterset_class()` method."
            % self.__class__.__name__
        )
        return self.filterset_class

    def get_pagination_metadata(self):
        return dict()

    def get_info_for_exception(self, e):
        return {
            'detail': str(e)
        }

    def get_paginated_response(self, data):
        """
        Overridden to allow subclasses the opportunity to include
        additional metadata in the paginated response
        """
        assert self.paginator is not None

        return self.paginator.get_paginated_response(
            data,
            self.get_pagination_metadata()
        )

    def get_detail_serializer_class(self):
        if not self.serializers:
            return super().get_serializer_class()

        try:
            return self.serializers['retrieve']
        except KeyError:
            return self.serializers['default']

    def get_detailed_response_context(self, request, instance):
        return self.get_serializer_context()

    def perform_create(self, serializer):
        """
        Overridden to disallow the creation of duplicate records.
        """
        if not self.allow_duplicate_records:
            ModelClass = serializer.Meta.model
            filter_param_names = primitive_attribute_names(ModelClass)
            filter_params = filter_dict(serializer.validated_data, filter_param_names)
            if filter_params:
                try:
                    ModelClass.objects.get(**filter_params)
                    raise exceptions.ValidationError({
                        api_settings.NON_FIELD_ERRORS_KEY: 'E_CREATE_DUPLICATE_RECORD',
                    })
                except (FieldError, ModelClass.DoesNotExist):
                    pass

        super().perform_create(serializer)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        When a record is created we want to send back its full details
        regardless of which serializer was used to perform the creation.
        """
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)

        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: getattr(create_serializer.instance, self.lookup_field)}
        try:
            obj = queryset.get(**filter_kwargs)
        except ObjectDoesNotExist:
            raise exceptions.NotFound()

        DetailSerializerClass = self.get_detail_serializer_class()
        detail_serializer = DetailSerializerClass(
            instance=obj,
            context=self.get_detailed_response_context(
                request=create_serializer.context['request'],
                instance=obj
            )
        )
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        When a record is updated we want to send back its full details
        regardless of which serializer was used to perform the modification.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        update_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        self.perform_update(update_serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        DetailSerializerClass = self.get_detail_serializer_class()
        detail_serializer = DetailSerializerClass(
            instance=update_serializer.instance,
            context=self.get_detailed_response_context(
                request=update_serializer.context['request'],
                instance=update_serializer.instance
            )
        )
        return Response(detail_serializer.data)

    @action(detail=False, methods=['get'])
    def filter_options(self, request, *args, **kwargs):
        """
        Specifies available filtration parameters for a given entity.
        """
        FilterSetClass = self.get_filterset_class()
        metadata_instance = self.metadata_class()
        serializer = self.get_serializer()
        serializer_info = metadata_instance.get_serializer_info(serializer)
        options_info = FilterSetClass.get_options_info(self, serializer_info)

        return Response(options_info, status=status.HTTP_200_OK)

    def filter_list_queryset(self, request, queryset):
        """
        The base MasterDetailViewSet performs no filtering at all.
        Subclasses may override this method to further limit the
        queryset based on the context of the given request.
        """
        return queryset

    def restrict_list_queryset(self, request, queryset):
        """
        The base MasterDetailViewSet performs no restriction at all.
        Subclasses may override this method to further limit the
        queryset based on the context of the given request.
        """
        return queryset


# ------------------------------------------------------------------------------
class AttachmentViewSet(mixins.DocumentViewSetMixin, MasterDetailViewSet):
    queryset = Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer


class MediaAttachmentViewSet(mixins.DocumentViewSetMixin, MasterDetailViewSet):
    queryset = MediaAttachment.objects.all()
    serializers = {
        'default': serializers.MediaAttachmentSerializer,
        'retrieve': serializers.MediaAttachmentSerializer,
        'update': serializers.MediaAttachmentEditSerializer,
    }


class NoteViewSet(mixins.DocumentViewSetMixin, MasterDetailViewSet):
    allow_duplicate_records = True
    filterset_class = filters.NoteFilter
    ordering = '-date_created'
    queryset = Note.objects.all()
    search_fields = (
        'created_by__first_name', 'created_by__last_name',
        'subject', 'text',
    )
    serializers = {
        'retrieve': serializers.NoteDetailSerializer,
        'default': serializers.NoteListSerializer,
    }
