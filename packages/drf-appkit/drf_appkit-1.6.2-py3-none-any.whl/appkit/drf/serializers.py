import copy

from django.contrib.auth import get_user_model

from rest_framework import serializers

from djoser.conf import settings as djoser_settings
from djoser.serializers import SendEmailResetSerializer as BaseSendEmailResetSerializer

User = get_user_model()


class IntegerListField(serializers.ListField):
    child = serializers.IntegerField()


class StringListField(serializers.ListField):
    child = serializers.CharField()


class ContentTypeSerializer(serializers.CharField):
    def to_representation(self, value):
        return value.name


class AttributedHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    def to_representation(self, value):
        hyperlink = super().to_representation(value)
        return {
            'id': value.pk,
            'url': hyperlink,
            'path': value.path,
            'label': str(value),
        }


class GroupListField(serializers.BaseSerializer):
    child = None

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None, '`child` is a required argument.'

        super().__init__(*args, **kwargs)

        self.child.bind(field_name='', parent=self)

    def to_representation(self, value):
        grouped_items = []

        for group_name, items in value:
            child_items = self.child.to_representation(items)
            grouped_items.append((group_name, child_items))

        return grouped_items


class SendEmailResetSerializer(BaseSendEmailResetSerializer):
    def get_user(self, is_active=True):
        try:
            email_param = '{}__iexact'.format(self.email_field)
            user_filter_params = {
                'is_active': is_active,
                email_param: self.data.get(self.email_field, ""),
            }
            user = User._default_manager.get(**user_filter_params)
            if user.has_usable_password():
                return user
        except User.DoesNotExist:
            pass
        if (
            djoser_settings.PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND
            or djoser_settings.USERNAME_RESET_SHOW_EMAIL_NOT_FOUND
        ):
            self.fail("email_not_found")
