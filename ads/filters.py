from django_filters import filters
from django_filters.rest_framework import FilterSet


class AdFilter(FilterSet):
    location = filters.CharFilter(lookup_expr='icontains')
