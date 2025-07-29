from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from rest_framework.test import (
    APIRequestFactory,
    APITestCase as DRFAPITestCase,
)
from rest_framework_simplejwt.tokens import RefreshToken

from ..auth import get_userprofile_model
from ..models import Document

User = get_user_model()
UserProfile = get_userprofile_model()


SINGLE_LINE_STRING = 'Just an ordinary little sentence.'

MULTILINE_STRING = """
This is a string that is separated into
multiple lines via the newline character.
It may be used in a situation where a body
of text is expected (such as a comment).
"""


class TestCaseAssertionMixin(object):
    """
    A mixin to provide additional test assertions that specifically applicable
    to django-rest-framework responses.
    """
    def assertReturnListContains(self, return_list, record):
        """
         Helper method to test whether a given ReturnList
        (typically generated in response to an API request)
         contains a given record.
         Test is based on whether or not a record in the given
         return_list has an ID equal to the given record.
        """
        try:
            list(map(lambda i: i['id'], return_list)).index(record.id)
            return
        except ValueError:
            self.fail('item "{}" not found in list'.format(record))

    def assertNotReturnListContains(self, return_list, record):
        """
         Helper method to test whether a given ReturnList
        (typically generated in response to an API request)
         contains a given record.
         Test is based on whether or not a record in the given
         return_list has an ID equal to the given record.
        """
        try:
            list(map(lambda i: i['id'], return_list)).index(record.id)
            self.fail('item "{}" was found in list'.format(record))
        except ValueError:
            return



class APITestCase(TestCaseAssertionMixin, DRFAPITestCase):
    def _logout(self):
        self.access_token = None
        self.refresh_token = None

    def setUp(self):
        super().setUp()
        self._logout()

    def url_namespace(self):
        return None

    def url_reverse(self, url_info):
        view_name = url_info if isinstance(url_info, str) else url_info[0]
        url_namespace = self.url_namespace()
        if url_namespace:
            view_name = '{}:{}'.format(url_namespace, view_name)

        url_kwargs = url_info[1] if isinstance(url_info, tuple) else {}

        return reverse(view_name, kwargs=url_kwargs)

    def detail_url(self, model, **kwargs):
        url_kwargs = {**kwargs}

        if isinstance(model, models.Model):
            model_name = model._meta.model_name
            if not url_kwargs:
                if isinstance(model, Document):
                    url_kwargs['uuid'] = str(model.uuid)
                else:
                    url_kwargs['pk'] = model.pk
        else:
            model_name = model

        return self.url_reverse((f'{model_name}-detail', url_kwargs))

    def api_request(self, request_method, url, params=None, **kwargs):
        request_kwargs = {'format': 'json', **kwargs}

        if self.access_token:
            request_kwargs['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(self.access_token)

        if request_method == 'GET':
            return self.client.get(url, params, **request_kwargs)
        elif request_method == 'POST':
            return self.client.post(url, params, **request_kwargs)
        elif request_method == 'PUT':
            return self.client.put(url, params, **request_kwargs)
        elif request_method == 'PATCH':
            return self.client.patch(url, params, **request_kwargs)
        elif request_method == 'DELETE':
            return self.client.delete(url, params, **request_kwargs)
        elif request_method == 'OPTIONS':
            return self.client.options(url, params, **request_kwargs)
        else:
            raise RuntimeError('Request method not supported: {}'.format(request_method))

    def api_get(self, url_info, params=None, **kwargs):
        return self.api_request('GET', self.url_reverse(url_info), params, **kwargs)

    def api_post(self, url_info, params=None, **kwargs):
        return self.api_request('POST', self.url_reverse(url_info), params, **kwargs)

    def api_put(self, url_info, params=None, **kwargs):
        return self.api_request('PUT', self.url_reverse(url_info), params, **kwargs)

    def api_patch(self, url_info, params=None, **kwargs):
        return self.api_request('PATCH', self.url_reverse(url_info), params, **kwargs)

    def api_delete(self, url_info, params=None, **kwargs):
        return self.api_request('DELETE', self.url_reverse(url_info), params, **kwargs)

    def api_options(self, url_info, params=None, **kwargs):
        return self.api_request('OPTIONS', self.url_reverse(url_info), params, **kwargs)

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

    def serialize(self, instance, type, serializer_class):
        factory = APIRequestFactory()
        request = factory.get(self.detail_url(type, pk=instance.pk))
        serializer = serializer_class(instance=instance, context={
            'request': request
        })
        return serializer.data


