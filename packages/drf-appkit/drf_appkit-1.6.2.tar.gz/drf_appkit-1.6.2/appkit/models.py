import os
import uuid

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.files.storage import FileSystemStorage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.signing import Signer
from django.db import models
from django.db.models.signals import ModelSignal
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from django.contrib.gis.db.models import PointField

from djmoney.models.fields import MoneyField
from notificationcenter.models import default_center as notification_center
from treebeard.mp_tree import MP_Node
from versatileimagefield.fields import VersatileImageField

from .managers import DocumentManager
from .storages import MediaStorage
from .util import (
    bumpy_case_words,
    UploadMediaAttachmentTo,
    UploadSecureAttachmentTo,
)

from .settings import appkit_settings


class DRFModelMixin:
    notification_classes = {}

    @classmethod
    def include_related_users_as_notification_subscribers(cls, recipients, notification_name, sender):
        """
         Implicitly include a document's assigned recipients in the set of notification subscribers
        """
        if sender:
            recipients.update(sender.related_users)

    def get_detail_url_name(self):
        if hasattr(self, 'detail_url_name'):
            return getattr(self, 'detail_url_name')

        return f'{self._meta.app_label}:{self._meta.model_name}:read'

    def get_absolute_url(self):
        detail_url_name = self.get_detail_url_name()
        return reverse(detail_url_name, kwargs={'uuid': self.uuid})

    # DRY-rest-permissions
    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_write_permission(request):
        return True

    def has_object_write_permission(self, request):
        return True

    @property
    def content_type_name(self):
        return str(self._meta)

    @property
    def informal_description(self):
        """
        Return the class name as a string of lowercase words. Used in construction
        of comment email body.
        """
        return " ".join([w.lower() for w in bumpy_case_words(self.__class__.__name__)])

    def clone(self):
        """
        Returns: a new model instance with all of its direct field values set
        to those of this model.
        """
        ModelClass = self._meta.model
        model_fields = ModelClass._meta.get_fields()

        duplicate = ModelClass()

        for field in model_fields:
            field_name = field.name

            if (isinstance(field, GenericRelation)
                or field.one_to_many
                or field.auto_created
                or field.many_to_many
                or field.one_to_one
            ):
                continue

            record_value = getattr(self, field_name)
            setattr(duplicate, field_name, record_value)

        duplicate.save()
        return duplicate

    @property
    def related_users(self):
        return set()

    def notification_subscribers(self, event_name=None, digest=None):
        notification_name = self.notification_name_for_event(event_name)
        if digest is None:
            return notification_center.subscribers(notification_name, sender=self, digest=True) | \
                   notification_center.subscribers(notification_name, sender=self, digest=False)

        return notification_center.subscribers(notification_name, sender=self, digest=digest)

    @property
    def all_subscribers(self):
        return self.notification_subscribers()

    @property
    def alert_subscribers(self):
        return self.notification_subscribers(digest=False)

    @property
    def digest_subscribers(self):
        return self.notification_subscribers(digest=True)

    def notification_name_for_event(self, event_name=None):
        content_type = ContentType.objects.get_for_model(self)
        name_components = [content_type.app_label, content_type.model]
        if event_name is not None:
            if isinstance(event_name, str):
                name_components.append(event_name)
            else:
                raise TypeError('event_name expected to be of type string. Got %s' % type(event_name))

        return ':'.join(name_components)


    def notify_users(self, event_type, date_scheduled=None, **kwargs):
        """
        Perform notification(s) in response to the given event type.
        """
        created_by = None
        request = kwargs.get('request')
        if request and request.user.is_authenticated:
            created_by = request.user

        notification_center.post_notification(
            self.notification_name_for_event(event_type),
            created_by,
            self,
            context={'date_scheduled': date_scheduled}
        )


class ModelBase(DRFModelMixin, models.Model):
    class Meta:
        abstract = True


class Place(ModelBase):
    place_id = models.CharField(max_length=255, unique=True)
    geoposition = PointField(geography=True)

    info = models.JSONField()
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=2, blank=True)
    country = models.CharField(max_length=30, blank=True)
    postal_code = models.CharField(max_length=7, blank=True)

    def __str__(self):
        if 'formatted_address' in self.info:
            return self.info['formatted_address']
        return self.place_id

    def format(self, *component_types):
        try:
            address_components = self.info['address_components']
        except KeyError:
            return self.info.get('formattedAddress')

        address_parts = []
        for component_type in component_types:
            for address_component in address_components:
                if component_type in address_component['types']:
                    address_parts.append(address_component['short_name'])
        return ', '.join(address_parts)


class Region(MP_Node):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, blank=False, default=None)
    code = models.CharField(max_length=4, blank=True)
    place = models.ForeignKey(Place, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        name_components = [d.name for d in self.get_ancestors()]
        name_components.append(self.name)
        return ' - '.join(name_components)

    @property
    def root_name(self):
        return self.get_root().name

    @property
    def children(self):
        return self.get_children()


class Tag(MP_Node):
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=20, blank=True, null=True)
    purpose = models.CharField(max_length=255, blank=True, null=True)
    position = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ('name', 'type',)

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        name_components = [d.name for d in self.get_ancestors()]
        name_components.append(self.name)
        return ' - '.join(name_components)

    @property
    def root_name(self):
        return self.get_root().name


class Document(ModelBase):
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_modified = models.DateTimeField(auto_now=True, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_created_by',
        on_delete=models.PROTECT,
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    site = models.ForeignKey(Site, on_delete=models.PROTECT)

    objects = DocumentManager()

    class Meta:
        abstract = True

    @staticmethod
    def merge_strategy():
        return {}

    def get_media_attachment_directory(self, attachment):
        model_name = slugify(self._meta.verbose_name)
        return os.path.join(model_name, str(self.uuid))


def get_attachment_file_storage():
    return FileSystemStorage(location=settings.SECURE_MEDIA_ROOT)


class Attachment(Document):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('content_type', 'object_id')
    file = models.FileField(
        upload_to=UploadSecureAttachmentTo('attachments'),
        max_length=255,
        storage=get_attachment_file_storage,
    )

    signer = Signer(sep='/', salt='appkit.Attachment')

    def __str__(self):
        return self.file.name

    def basename(self):
        return os.path.basename(self.file.name)

    def media_root(self):
        if not hasattr(self.object, 'get_media_attachment_directory'):
            return ''
        return self.object.get_media_attachment_directory(self)


class MediaTypeChoices(models.TextChoices):
    AUDIO = 'audio', _('Audio')
    IMAGE = 'image', _('Image')
    VIDEO = 'video', _('Video')


class MediaAttachmentManager(models.Manager):
    def ready_videos(self):
        return self.filter(media_type=MediaTypeChoices.VIDEO, attributes__mux__status='ready')


class MediaAttachment(Document):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('content_type', 'object_id')
    attributes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    media_type = models.CharField(choices=MediaTypeChoices.choices, max_length=5)
    image = VersatileImageField(max_length=255, storage=MediaStorage(), upload_to=UploadMediaAttachmentTo())
    width = models.IntegerField()
    height = models.IntegerField()
    placeholder = models.CharField(max_length=128, blank=True, null=True, help_text='Low-resolution image produced using blurhash')

    position = models.IntegerField(default=0)
    label = models.CharField(max_length=30, blank=True)
    rendition_key = models.CharField(max_length=20, blank=False, null=True)
    warm = models.BooleanField(default=False, help_text='Indicates whether renditions have been created')

    objects = MediaAttachmentManager()

    class Meta:
        ordering = ('position',)

    def __str__(self):
        description = super().__str__()

        if self.label:
            description += ': {}'.format(self.label)

        return description


    @property
    def media_url(self):
        media_root = ''
        if hasattr(self.object, 'media_root'):
            media_root = self.object.media_root()

        return media_root + self.get_absolute_url()


class Note(Document):
    class Meta:
        ordering = ('-date_created',)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('content_type', 'object_id')

    subject = models.CharField(max_length=255)
    text = models.TextField(blank=True, default='')

    attachments = GenericRelation(Attachment)

    def __str__(self):
        return self.subject


class Thing(models.Model):
    attributes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    attachments = GenericRelation(Attachment)
    media_attachments = GenericRelation(MediaAttachment)
    notes = GenericRelation(Note)
    feature_image = models.OneToOneField(MediaAttachment, blank=True, null=True, on_delete=models.SET_NULL)
    place = models.ForeignKey(Place, blank=True, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.SET_NULL)
    geoposition = PointField(geography=True, blank=True, null=True)

    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AbstractProduct(Thing):
    price = MoneyField(max_digits=14, decimal_places=2, blank=True, null=True, default_currency=None)
    sku = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        abstract = True


class Arrangement(Document):
    name = models.CharField(max_length=100)
    item_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL)
    attributes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    def __str__(self):
        if self.item_type:
            return f'{self.name} ({self.item_type})'
        return self.name


class ArrangementItem(Document):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    represented_object = GenericForeignKey('content_type', 'object_id')

    position = models.SmallIntegerField(default=0)
    arrangement = models.ForeignKey(Arrangement, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return str(self.represented_object)

    class Meta:
        ordering = ('position',)


class SiteAlias(ModelBase):
    domain = models.CharField(max_length=100, unique=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='aliases')

    class Meta:
        verbose_name_plural = _('Site Aliases')


# ------------------------------------------------------------------------------
document_event = ModelSignal(use_caching=True)

get_current_site = appkit_settings.CURRENT_SITE_ACCESSOR
