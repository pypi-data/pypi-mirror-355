import logging
import reversion
import uuid
from collections import defaultdict

from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    Group,
    Permission as DjangoPermission,
)
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions

from rest_framework import exceptions, serializers
from rest_framework_recursive.fields import RecursiveField
from rest_framework.serializers import ImageField

from djoser.conf import settings as djoser_settings
from djoser.serializers import (
    ActivationSerializer as DjoserActivationSerializer,
    UserCreateSerializer as DjoserUserCreateSerializer,
)

from phonenumber_field.serializerfields import PhoneNumberField

from versatileimagefield.utils import (
    build_versatileimagefield_url_set,
    get_rendition_key_set,
)

from ..auth import get_userprofile_model

from ..drf.fields import (
    UUIDListField,
)

from ..drf.fields import (
    AttachmentFileField,
    DocumentPathField,
    ContentTypeField,
)

from ..models import (
    ArrangementItem,
    Attachment,
    MediaAttachment,
    Note,
    Place,
    Region,
    SiteAlias,
    Tag,
)

from ..settings import appkit_settings
from ..shortcuts import image_variation_size

User = get_user_model()
UserProfile = get_userprofile_model()

get_current_site = appkit_settings.CURRENT_SITE_ACCESSOR


class PermissionsMixin(object):
    def get_permissions(self, obj):
        if isinstance(obj, Group):
            permissions = obj.permissions.all()
        else:
            permissions = obj.user_permissions.all()

        permission_map = defaultdict(set)
        for ModelClass in self.managed_model_classes(obj):
            content_type = ContentType.objects.get_for_model(ModelClass)
            model_permissions = DjangoPermission.objects.filter(content_type=content_type)
            for permission in model_permissions:
                if permission in permissions:
                    permission_name = '{app_label}.{codename}'.format(
                        app_label=content_type.app_label,
                        codename=permission.codename
                    )
                    permission_map[content_type.id].add(permission_name)

        return permission_map


class PermissionSerializer(serializers.Serializer):
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all()
    )
    permission_name = serializers.CharField()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        _, codename = attrs['permission_name'].split('.')
        attrs['permission'] = DjangoPermission.objects.get(
            codename=codename,
            content_type=attrs['content_type'],
        )
        return attrs


class SiteAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteAlias
        fields = ('domain',)


class SiteSerializer(serializers.ModelSerializer):
    aliases = SiteAliasSerializer(many=True)
    public_url = serializers.SerializerMethodField('get_public_url')

    class Meta:
        model = Site
        fields = (
            'aliases', 'domain', 'name', 'public_url',
        )
        
    def get_public_url(self, instance):
        request = self.context['request']

        if instance.aliases.exists():
            site_alias = instance.aliases.first()
            domain = site_alias.domain
        else:
            domain = instance.domain
        return f'{request.scheme}://{domain}'


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'url', 'name',)


class PlaceSerializer(serializers.ModelSerializer):
    info = serializers.JSONField(read_only=True)
    place_id = serializers.CharField(read_only=True)

    class Meta:
        model = Place
        fields = (
            'place_id', 'info',
            'city', 'state', 'country', 'postal_code',
        )


class RegionSerializer(serializers.HyperlinkedModelSerializer):
    children = serializers.ListSerializer(child=RecursiveField())

    class Meta:
        model = Region
        fields = ('id', 'url', 'name', 'full_name', 'root_name', 'children')


class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id', 'url', 'name', 'depth', 'path',
            'type', 'purpose', 'position',
        )


class UserListSerializer(serializers.HyperlinkedModelSerializer):
    content_type = ContentTypeField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'url', 'content_type', 'is_active', 'is_staff',
            'email', 'first_name', 'last_name', 'full_name',
        )
        
        
class MediaAttachmentImageSerializer(ImageField):
    def to_representation(self, value):
        media_attachment = value.instance

        if not (media_attachment.rendition_key and media_attachment.warm):
            return super().to_representation(value)

        try:
            natural_width = media_attachment.width
            natural_height = media_attachment.height
            sizes = get_rendition_key_set(media_attachment.rendition_key)

            context_request = None
            if self.context:
                context_request = self.context.get('request', None)
            url_set = build_versatileimagefield_url_set(value, sizes, request=context_request)

            repr = {}
            for image_key, image_name in sizes:
                image_width, image_height = image_variation_size(image_name, natural_width, natural_height)
                repr[image_key] = {
                    'src': url_set[image_key],
                    'w': image_width,
                    'h': image_height,
                }
            return repr
        except (FileNotFoundError, ValueError) as e:
            # This event should NEVER happen. If it ever does, we need to know about it.
            logger = logging.getLogger("integrity")
            logger.log(logging.ERROR, str(e))
            return super().to_representation(value)


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    """
    Override the create method to automatically set the created_by field to the
    authenticated user who issued the request
    """
    created_by = UserListSerializer(read_only=True)
    content_type = ContentTypeField(read_only=True)
    path = DocumentPathField(max_length=100, read_only=True)

    class Meta:
        fields = (
            'id', 'uuid', 'url', 'site', 'path', 'content_type',
            'created_by', 'date_created', 'date_modified',
        )

    def create(self, validated_data):
        """
        Override the create method to automatically set the created_by field to the
        authenticated user who issued the request
        """
        request = self.context.get('request')
        if not request and request.user.is_authenticated:
            raise exceptions.NotAuthenticated('Documents can only be created by an authenticated user')

        validated_data.update({
            'created_by_id': request.user.pk,
            'site': get_current_site(request),
        })

        return super().create(validated_data)

    def save(self, **kwargs):
        """
        Override the save method to create a new revision whenever a document
        is created or updated
        """
        with reversion.create_revision():
            instance = super().save(**kwargs)

            request = self.context.get('request')
            if request:
                reversion.set_user(request.user)

            if request.method == 'POST':
                reversion.set_comment('Initial version.')

            if request.method == 'PATCH':
                reversion.set_comment(','.join(self.validated_data.keys()))

            return instance


class AttachmentSerializer(DocumentSerializer):
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all()
    )

    media_url = AttachmentFileField(read_only=True)

    class Meta(DocumentSerializer.Meta):
        model = Attachment
        fields = DocumentSerializer.Meta.fields + (
            'content_type', 'media_url', 'object_id',
        )


class MediaAttachmentSerializer(DocumentSerializer):
    class Meta(DocumentSerializer):
        model = MediaAttachment
        fields = DocumentSerializer.Meta.fields + (
            'image', 'position', 'label', 'width', 'height',
        )

# ------------------------------------------------------------------------------
# List Serializers
# ------------------------------------------------------------------------------
class UserProfileListSerializer(DocumentSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = DocumentSerializer.Meta.fields + (
            'user', 'phone',
        )


class NoteListSerializer(DocumentSerializer):
    created_by = UserListSerializer(read_only=True)

    class Meta:
        model = Note
        fields = DocumentSerializer.Meta.fields + (
            'created_by', 'subject', 'text',
        )


class UserSetSerializer(serializers.Serializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
    )

    class Meta:
        fields = ('users',)


# ------------------------------------------------------------------------------
# Detail & Update Serializers
# ------------------------------------------------------------------------------
class GroupDetailSerializer(PermissionsMixin, GroupSerializer):
    permissions = serializers.SerializerMethodField('get_permissions')
    user_set = UserListSerializer(read_only=True, many=True)

    class Meta(GroupSerializer.Meta):
        fields = GroupSerializer.Meta.fields + (
            'permissions', 'user_set',
        )

    def managed_model_classes(self, group):
        return []


class UserDetailSerializer(PermissionsMixin, UserListSerializer):
    groups = GroupDetailSerializer(read_only=True, many=True)
    permissions = serializers.SerializerMethodField('get_permissions')

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + (
            'groups', 'permissions',
        )

    def managed_model_classes(self, user):
        return []


class NoteDetailSerializer(NoteListSerializer):
    people = UserProfileListSerializer(read_only=True, many=True)

    class Meta(NoteListSerializer.Meta):
        fields = NoteListSerializer.Meta.fields + (
            'people',
        )


class UserProfileDetailSerializer(UserProfileListSerializer):
    created_by = UserListSerializer(read_only=True)
    user = UserDetailSerializer(read_only=True)

    class Meta(UserProfileListSerializer.Meta):
        fields = UserProfileListSerializer.Meta.fields + (
            'created_by',
        )

# ------------------------------------------------------------------------------
# DJOSER Subclasses
# ------------------------------------------------------------------------------
class UserCreateSerializer(DjoserUserCreateSerializer):
    profile = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            User._meta.pk.name, 'email', 'password', 'profile',
        )

    def validate_email(self, value):
        try:
            User.objects.get(email__iexact=value)
            raise serializers.ValidationError('A user with email address "{}" already exists'.format(value))
        except User.DoesNotExist:
            return value


    def validate(self, attrs):
        validated_data = super().validate(attrs)

        # The 'username' field is not utilized by this application but we'll
        # still allow it to serve as a unique identifier.
        # Users are typically identified by their associated email address.
        validated_data['username'] = uuid.uuid1()

        return validated_data


class ActivationSerializer(DjoserActivationSerializer):
    default_error_messages = {
        "password_mismatch": djoser_settings.CONSTANTS.messages.PASSWORD_MISMATCH_ERROR
    }

    new_password = serializers.CharField(style={"input_type": "password"})
    re_new_password = serializers.CharField(style={"input_type": "password"})
    phone = PhoneNumberField()

    def validate(self, attrs):
        user = self.context["request"].user or self.user
        assert user is not None

        attrs = super().validate(attrs)

        try:
            validate_password(attrs["new_password"], user)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        if attrs["new_password"] != attrs["re_new_password"]:
            error_messages = [self.default_error_messages['password_mismatch']]
            raise serializers.ValidationError({"re_new_password": error_messages})

        return attrs


# ------------------------------------------------------------------------------
# Miscellaneous
# ------------------------------------------------------------------------------
class MediaAttachmentEditSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MediaAttachment
        fields = (
            'id', 'url', 'position', 'label',
        )


class MediaAttachmentBulkDeleteSerializer(serializers.Serializer):
    uuids = UUIDListField()


class MediaAttachmentBulkRepositionSerializer(serializers.Serializer):
    uuids = UUIDListField()
    
    
class ArrangementItemBulkRepositionSerializer(serializers.Serializer):
    items = serializers.HyperlinkedRelatedField(
        queryset=ArrangementItem.objects.all(),
        view_name='arrangementitem-detail',
        lookup_field='uuid',
        many=True,
    )


class ForcePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"})
    re_new_password = serializers.CharField(style={"input_type": "password"})
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        queryset=User.objects.all(),
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        try:
            user = attrs['user']
            validate_password(attrs["new_password"], user)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        if attrs["new_password"] != attrs["re_new_password"]:
            raise serializers.ValidationError({"re_new_password": list('The given passwords do not match')})

        return attrs
