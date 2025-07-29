from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site

import rest_framework_filters as filters

from ..auth import get_userprofile_model

from ..drf.filters import ComplexOrderingFilter, FilterSet
from ..shortcuts import create_date_range_choices

from ..models import (
    Arrangement,
    Note,
    Region,
    Tag,
)

User = get_user_model()
UserProfile = get_userprofile_model()


def choices_for_region():
    regions = Region.objects.all().order_by('depth', 'path')
    region_choices = [{ 'value': str(d.id), 'label': str(d) } for d in regions]
    region_choices.insert(0, {
        'label': '-- None --',
        'value': 'null',
    })
    return region_choices


class DocumentFilter(FilterSet):
    date_created = filters.DateFromToRangeFilter()
    date_modified = filters.DateFromToRangeFilter()


class GroupFilter(FilterSet):
    class Meta:
        model = Group
        fields = {
            'id': ('exact', 'in',),
            'name': ('exact', 'in',),
        }


class NoteFilter(FilterSet):
    class Meta:
        model = Note
        fields = {
            'id': ('exact', 'in',),
            'subject': ('icontains',),
            'text': ('icontains',),
        }


class RegionFilter(FilterSet):
    class Meta:
        model = Region
        fields = {
            'id': ('exact', 'in',),
            'depth': ('exact', 'in',),
            'path': ('exact', 'startswith',),
        }


class SiteFilter(FilterSet):
    class Meta:
        model = Site
        fields = {
            'id': ('exact', 'in',),
            'name': ('exact',),
            'domain': ('exact',),
        }


class TagFilter(FilterSet):
    class Meta:
        model = Tag
        fields = {
            'id': ('exact', 'in',),
            'name': ('exact',),
            'type': ('exact',),
            'depth': ('exact', 'in',),
            'path': ('exact', 'startswith',),
        }


class UserFilter(FilterSet):
    groups = filters.RelatedFilter(
        GroupFilter,
        queryset=Group.objects.all()
    )

    class Meta:
        model = User
        fields = {
            'id': ('exact', 'in',),
            'is_active': ('exact',),
            'is_staff': ('exact',),
            'first_name': ('exact', 'startswith', 'icontains'),
            'last_name': ('exact', 'startswith', 'icontains'),
            'username': ('exact', 'startswith', 'icontains'),
            'email': ('exact', 'startswith', 'icontains'),
        }


class ArrangementFilter(DocumentFilter):
    order = ComplexOrderingFilter(
        fields=('date_created', 'date_modified', 'name'),
        arrangement=(
            ('name', 'Alphabetical'),
            ('-date_modified', 'Recently Modified'),
            ('-date_created', 'Date Added (newest to oldest)'),
        )
    )

    class Meta:
        model = Arrangement
        fields = {
            'id': ('exact', 'in',),
            'item_type': ('exact',),
            'name': ('exact',),
        }

    @classmethod
    def field_arrangement(cls, request):
        return [
            {'name': 'search', 'label': 'Search Term', 'widget': 'searchfield'},

            {
                'name': 'date_created',
                'widget': {
                    'type': 'daterangepicker',
                    'choices': create_date_range_choices(),
                }
            },
            {'name': 'date_created_before', 'widget': 'hidden'},
            {'name': 'date_created_after', 'widget': 'hidden'},
        ]


# class UserProfileFilter(DocumentFilter):
#     user = filters.RelatedFilter(
#         UserFilter,
#         queryset=User.objects.all()
#     )
#
#     class Meta:
#         model = UserProfile
#         fields = {
#             'id': ('exact', 'in',),
#             'date_created': ('exact',),
#             'phone': ('exact', 'startswith', 'icontains'),
#         }
#
#     @classmethod
#     def field_arrangement(self, request):
#         return [
#             {'name': 'search', 'label': 'Search Term', 'widget': 'searchfield'},
#             {'name': 'user__is_active', 'label': 'Status', 'widget': 'radiogroup', 'choices': [
#                 {'label': 'Active', 'value': 'true'},
#                 {'label': 'Inactive', 'value': 'false'},
#             ]},
#             {
#                 'name': 'date_created',
#                 'widget': 'daterangepicker',
#                 'choices': choices_for_date_created(90)
#             },
#             {'name': 'date_created_before', 'widget': 'hidden'},
#             {'name': 'date_created_after', 'widget': 'hidden'},
#         ]
