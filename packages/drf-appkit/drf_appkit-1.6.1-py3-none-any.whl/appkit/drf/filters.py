import operator
import re
from functools import reduce

from django.db import models
from django.db.models.functions import Lower
from django.db.models.constants import LOOKUP_SEP

from rest_framework.filters import (
    OrderingFilter as DRFOrderingFilter,
    SearchFilter as DRFSearchFilter,
)

import rest_framework_filters
from rest_framework_filters import FilterSet as RestFrameworkFilterSet
from rest_framework_filters.filters import OrderingFilter as RestFrameworkOrderingFilter

from dry_rest_permissions.generics import DRYPermissionFiltersBase

YES_NO_CHOICES = [
    {'value': 'true', 'label': 'Yes'},
    {'value': 'false', 'label': 'No'},
]

YES_NO_CHOICES_INVERTED = [
    {'value': 'false', 'label': 'Yes'},
    {'value': 'true', 'label': 'No'},
]

class CaseInsensitiveOrderingFilter(DRFOrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            new_ordering = []
            for field in ordering:
                if field.startswith('-'):
                    new_ordering.append(Lower(field[1:]).desc())
                else:
                    new_ordering.append(Lower(field).asc())
            return queryset.order_by(*new_ordering)

        return queryset


class ComplexOrderingFilter(rest_framework_filters.OrderingFilter):
    def __init__(self, arrangement=None, *args, **kwargs):
        self.arrangement = arrangement
        super().__init__(*args, **kwargs)

    def get_arrangement(self, view):
        return self.arrangement

    def get_ordering_value(self, param):
        descending = param.startswith('-')
        param = param[1:] if descending else param
        field_name = self.param_map.get(param, param)

        if descending:
            return models.F(field_name).desc(nulls_last=True)
        else:
            return field_name


class SearchFilter(DRFSearchFilter):
    quoted_string_re = re.compile(r"\"(.+)\"")

    def get_search_terms(self, request):
        """
        Overridden to support the situation where we wish to search for an
        exact phrase (supplied as a quoted string)
        """
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')  # strip null characters

        match = self.quoted_string_re.match(params)
        if not match:
            return super().get_search_terms(request)

        return match[1]

    def construct_search(self, field_name, exact=False):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        elif exact:
            lookup = 'iexact'
        else:
            lookup = 'icontains'
        return LOOKUP_SEP.join([field_name, lookup])

    def transform_search_term(self, term_name, value):
        term_prefix = term_name[0:term_name.index(LOOKUP_SEP)]
        transform_method_name = f'transform_{term_prefix}'
        transform_method = getattr(self, transform_method_name, None)
        if transform_method:
            value = transform_method(value, term_name)

        return value

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        exact = False
        if isinstance(search_terms, str):
            exact = True
            search_terms = [search_terms]

        orm_lookups = [
            self.construct_search(str(search_field), exact)
            for search_field in search_fields
        ]

        base = queryset
        conditions = []
        for search_term in search_terms:
            queries = [models.Q(**{
                orm_lookup: self.transform_search_term(orm_lookup, search_term)
            }) for orm_lookup in orm_lookups]

            conditions.append(reduce(operator.or_, queries))
        queryset = queryset.filter(reduce(operator.and_, conditions))

        # Remove duplicates from results, if necessary
        if self.must_call_distinct(queryset, search_fields):
            # inspired by django.contrib.admin
            # this is more accurate than .distinct form M2M relationship
            # also is cross-database
            queryset = queryset.filter(pk=models.OuterRef('pk'))
            queryset = base.filter(models.Exists(queryset))

        return queryset


class FilterSet(RestFrameworkFilterSet):
    @classmethod
    def get_options_info(cls, view, serializer_info):
        primary_ordering = getattr(view, 'ordering', None)
        if isinstance(primary_ordering, tuple):
            primary_ordering = primary_ordering[0]

        options_info = {
            'ordering_fields': cls.ordering_field_arrangement(view),
            'extra_info': cls.extra_info(view),
            'primary_ordering': primary_ordering,
        }

        filter_fields = cls.field_arrangement(view)
        for field_info in filter_fields:
            if not isinstance(field_info, dict):
                continue

            field_name = field_info['name']
            field_metadata = serializer_info.get(field_name, {})

            if field_info.get('widget') == 'select':
                select_choices = field_info.get('choices')
                if select_choices is None:
                    field_choices = field_metadata.get('choices')
                    if field_choices:
                        select_choices = [{
                            'label': choice['display_name'],
                            'value': choice['value']
                        } for choice in field_choices]
                else:
                    select_choices = list(select_choices)

                if select_choices is None:
                    raise RuntimeError('Unable to establish choices for filter field: {}'.format(field_name))

                # Include a '--- None ---' option for fields that are nullable / not required
                if 'nullable' in field_info:
                    nullable = field_info['nullable']
                elif field_metadata.get('required') == False:
                    nullable = True
                else:
                    nullable = False

                if nullable:
                    select_choices.insert(0, {'label': '--- None ---', 'value': 'none'})

                field_info['choices'] = select_choices

        options_info['filter_fields'] = filter_fields

        return options_info

    @classmethod
    def field_arrangement(cls, request):
        return []

    @classmethod
    def extra_info(cls, view):
        return {}

    @classmethod
    def ordering_field_arrangement(cls, view):
        for declared_filter in cls.declared_filters.values():
            if isinstance(declared_filter, ComplexOrderingFilter):
                return declared_filter.get_arrangement(view)

            if isinstance(declared_filter, RestFrameworkOrderingFilter):
                return declared_filter.extra.get('choices')
        return None


class MasterDetailViewFilterBackend(DRYPermissionFiltersBase):
    def filter_list_queryset(self, request, queryset, view):
        queryset = view.filter_list_queryset(request, queryset)

        # Let subclasses define further restrictions
        return view.restrict_list_queryset(request, queryset)
