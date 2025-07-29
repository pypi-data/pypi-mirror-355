try:
    from collections import Iterable
except ImportError:
    from collections.abc import Iterable
    
from djmoney.contrib.django_rest_framework.fields import MoneyField
from drf_auto_endpoint.endpoints import Endpoint
from drf_auto_endpoint.get_field_dict import GetFieldDict
from drf_extra_fields.fields import DateTimeRangeField
from rest_framework import fields, relations


class DRFGetFieldDict(GetFieldDict):
    def get_base_dict_for_field(self, name, field_instance, translated_fields, serializer_instance):
        base_dict_for_field = super().get_base_dict_for_field(name, field_instance, translated_fields, serializer_instance)

        widget = 'textfield'

        if isinstance(field_instance, relations.ManyRelatedField):
            widget = 'itemlist'
        elif isinstance(field_instance, relations.HyperlinkedRelatedField):
            widget = 'select'
        elif field_instance.style.get('base_template') == 'textarea.html':
            widget = 'textarea'
        elif isinstance(field_instance, fields.DateField):
            widget = 'date'
        elif isinstance(field_instance, fields.DateTimeField):
            widget = 'datetime'
        elif isinstance(field_instance, DateTimeRangeField):
            widget = 'datetimerange'
        elif isinstance(field_instance, MoneyField):
            widget = 'money'

        base_dict_for_field['ui']['widget'] = widget

        return base_dict_for_field

get_field_dict = DRFGetFieldDict()


# ------------------------------------------------------------------------------
class DRFAutoEndpoint(Endpoint):
    def _get_field_dict(self, field, serializer_instance=None):
        foreign_key_as_list = (isinstance(self.foreign_key_as_list, Iterable) and field in self.foreign_key_as_list) \
            or (not isinstance(self.foreign_key_as_list, Iterable) and self.foreign_key_as_list)

        if serializer_instance is None:
            serializer_instance = self.get_serializer()()

        return get_field_dict(field, serializer_instance, self.get_translated_fields(),
                              self.fields_annotation, self.model, foreign_key_as_list=foreign_key_as_list)

