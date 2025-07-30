import datetime
import hashlib
import inspect
import ipaddress
import json
import logging
import os
import re
import string
import sys
import uuid

from urllib.parse import urlparse

from django.db import connections, models

from django.utils.deconstruct import deconstructible

from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import JSONField


GSM_7_CODES = {'0x40', '0xa3', '0x24', '0xa5', '0xe8', '0xe9', '0xf9', '0xec', '0xf2', '0xe7', '0x0a', '0xd8', '0xf8', '0x0d', '0xc5', '0xe5', '0x0394', '0x5f', '0x03a6', '0x0393', '0x039b', '0x03a9', '0x03a0', '0x03a8', '0x03a3', '0x0398', '0x039e', '0xa0', '0x0c', '0x5e', '0x7b', '0x7d', '0x5c', '0x5b', '0x7e', '0x5d', '0x7c', '0x20ac', '0xc6', '0xe6', '0xdf', '0xc9', '0x20', '0x21', '0x22', '0x23', '0xa4', '0x25', '0x26', '0x27', '0x28', '0x29', '0x2a', '0x2b', '0x2c', '0x2d', '0x2e', '0x2f', '0x30', '0x31', '0x32', '0x33', '0x34', '0x35', '0x36', '0x37', '0x38', '0x39', '0x3a', '0x3b', '0x3c', '0x3d', '0x3e', '0x3f', '0xa1', '0x41', '0x42', '0x43', '0x44', '0x45', '0x46', '0x47', '0x48', '0x49', '0x4a', '0x4b', '0x4c', '0x4d', '0x4e', '0x4f', '0x50', '0x51', '0x52', '0x53', '0x54', '0x55', '0x56', '0x57', '0x58', '0x59', '0x5a', '0xc4', '0xd6', '0xd1', '0xdc', '0xa7', '0xbf', '0x61', '0x62', '0x63', '0x64', '0x65', '0x66', '0x67', '0x68', '0x69', '0x6a', '0x6b', '0x6c', '0x6d', '0x6e', '0x6f', '0x70', '0x71', '0x72', '0x73', '0x74', '0x75', '0x76', '0x77', '0x78', '0x79', '0x7a', '0xe4', '0xf6', '0xf1', '0xfc', '0xe0', '0xa'}
GSM_7_SMS_UNIT_LENGTH = 160

def to_gsm7(val, max_length=None):
    gsm7_chars = []
    gsm7_length = 0

    for char in val:
        char_hex = hex(ord(char))
        if char_hex in GSM_7_CODES:
            gsm7_chars.append(char)
            gsm7_length += 1

        if max_length and gsm7_length == max_length:
            break

    return ''.join(gsm7_chars)


def bumpy_case_words(string):
    return [s for s in re.findall('([A-Z]*[a-z]*)', string) if len(s) > 0]


def string_with_unique_suffix(value, haystack):
    """
    Args:
        value: The string to generate a unique value for
        haystack: The set of strings to compare against for uniqueness

    Returns: The given value with a suffix index that renders it unique among the given set
    """
    haystack.sort()
    suffix = 1
    needle = value
    while needle in haystack:
        needle = '{}-{}'.format(value, suffix)
        suffix += 1

    return needle


def split_path(string, separator='/', count=1):
    """
    Given a path, return a tuple containing the specified number of initial elements
    and the remainder, which may be none.  Raises ValueError if the given path does
    not contain the specified number of components.

    e.g.

      > split_path('yabba/dabba/doo')
      ('yabba', 'dabba/doo')

      > split_path('yabba/dabba/doo', count=2)
      ('yabba', 'dabba', 'doo')

      > split_path('yabba.dabba.doo', '.', 3)
      ('yabba', 'dabba', 'doo', None)

    """
    result = []
    for i in range(0, count):
        if string is None:
            raise ValueError('empty path')
        index = string.find(separator)
        if index >= 0:
            result.append(string[:index])
            string = string[index+len(separator):]
        else:
            result.append(string)
            string = None
    result.append(string)
    return result


def path_components(string, separator='/'):
    """
    """
    element, rest = split_path(string, separator)
    if rest is None:
        return [element]
    return [element] + path_components(rest, separator)


def assign_timestamps(obj, date_created, date_modified):
    with connections[obj._state.db].cursor() as cursor:
        query_template = "UPDATE {trg_table_name} SET date_created='{date_created}',date_modified='{date_modified}' WHERE id={pk}"
        update_query = query_template.format(
            trg_table_name=obj._meta.db_table,
            pk=obj.pk,
            date_created=date_created.isoformat(),
            date_modified=date_modified.isoformat(),
        )
        return cursor.execute(update_query)


def sync_auto_timestamps(db, src, trg):
    fetch_query_template = "SELECT date_created,date_modified FROM {src_table_name} WHERE id={pk}"
    update_query_template = "UPDATE {trg_table_name} SET date_created='{date_created}',date_modified='{date_modified}' WHERE id={pk}"

    fetch_query = fetch_query_template.format(
        src_table_name=src._meta.db_table,
        pk=src.pk
    )
    db.execute(fetch_query)
    src_info = db.fetchone()

    update_query = update_query_template.format(
        trg_table_name=trg._meta.db_table,
        date_created=src_info[0],
        date_modified=src_info[1],
        pk=trg.pk
    )
    db.execute(update_query)


def value_for_attr_path(obj, attr_path):
    value = obj
    attributes = attr_path.split('.')
    for attribute in attributes:
        value = getattr(value, attribute)
    return value


def value_for_key_path(object, keypath, default=None, raise_exception=False):
    """
    Provide access to a property chain
    """
    target_object = object

    keys = keypath.split('.')
    for key in keys:
        try:
            if isinstance(target_object, dict):
                target_object = target_object[key]
            else:
                target_object = target_object.__getitem__(key)
        except (KeyError, AttributeError) as e:
            if raise_exception:
                raise KeyError('Keypath "{}" could not be resolved to a value'.format(keypath))
            return default

    return target_object


def filter_dict(value, keys):
    return {k: v for k, v in value.items() if k in keys}


def random_digest(digest_size=8):
    return hashlib.blake2s(digest_size=digest_size).hexdigest()


def top_level_domain(url):
    hostname = urlparse(url).hostname
    try:
        # If the hostname is an IP address, return it as-is
        ipaddress.IPv4Address(hostname)
        return hostname
    except ValueError:
        domain_parts = hostname.split('.')
        if len(domain_parts) > 2:
            domain_parts = domain_parts[-2:]
        return '.'.join(domain_parts)


class SimpleModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, models.Model):
            return str(obj)

        return super().default(obj)


def hashed_filename(image_file):
    hash = hashlib.blake2b(digest_size=4)
    if isinstance(image_file, str):
        with open(image_file, 'rb') as source_file:
            hash.update(source_file.read())
    else:
        hash.update(image_file.tobytes())
    return hash.hexdigest()


def primitive_attribute_names(ModelClass):
    """
    Given a django model class, return a list containing the names of all
    primitive fields (ex: strings, numbers, dates, booleans, etc).

    A primitive attribute is any field that _does not_ represent a relationship
    or complex data structure (ex: JSONField)
    """
    model_fields = ModelClass._meta.get_fields()
    return [field.name for field in model_fields if not (
            isinstance(field, GenericRelation)
            or isinstance(field, JSONField)
            or field.one_to_many
            or field.auto_created
            or field.many_to_many
            or field.one_to_one
    )]


@deconstructible
class UploadTo(object):
    """
    This class is used to generate a unique directory for uploaded files so as
    to avoid having to rename the uploaded file due to a name collision.
    An instance of this class may be supplied as the 'upload_to' parameter of
    a FileField whereby the given media_path_prefix is a subdirectory under the
    media root directory (ex: 'attachments', 'avatars', etc).
    """
    def __init__(self, media_path_prefix=None):
        self.media_path_prefix = media_path_prefix

    def upload_path(self, instance, filename):
        # To keep the paths a bit shorter, use only the last eight characters of
        # a generated UUID. It is _highly unlikely_ that the same character sequence
        # will be generated twice in one day.
        return os.path.join(
            datetime.datetime.today().strftime('%Y/%m/%d'),
            str(uuid.uuid4())[:8],
            filename
        )

    def __call__(self, instance, filename):
        path_components = [self.upload_path(instance, filename)]

        if self.media_path_prefix:
            path_components.insert(0, self.media_path_prefix)

        if os.environ.get('TEST'):
            path_components.insert(0, 'test')

        return os.path.join(*path_components)


@deconstructible
class UploadMediaAttachmentTo(UploadTo):
    def upload_path(self, attachment, filename):
        obj = attachment.object
        media_attachment_directory = obj.get_media_attachment_directory(attachment)
        return os.path.join(media_attachment_directory, filename)


@deconstructible
class UploadSecureAttachmentTo(UploadTo):
    def upload_path(self, attachment, filename):
        obj = attachment.object
        media_attachment_directory = obj.get_media_attachment_directory(attachment)

        return os.path.join(
            media_attachment_directory,
            filename
        )


def django_request_from_drf_request(request):
    django_request = request._request
    post_data = django_request.POST.copy()
    for k, v in request.data.items():
        post_data[k] = v
    django_request.POST = post_data
    return django_request
