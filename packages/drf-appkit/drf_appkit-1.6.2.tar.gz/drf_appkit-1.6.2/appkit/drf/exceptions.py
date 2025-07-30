from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    context['request']._request.drf_request = context['request']
    return response


class RecordExistsError(ValidationError):
    default_detail = _('Record already exists.')
    default_code = 'record_exists'
