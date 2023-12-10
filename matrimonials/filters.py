from django_filters import filters
from django_filters.rest_framework import FilterSet

from matrimonials.choices import EDUCATION_CHOICES, RELIGION_CHOICES


class MatrimonialFilter(FilterSet):
    age = filters.NumericRangeFilter(lookup_expr='range')
    religion = filters.ChoiceFilter(lookup_expr='exact', choices=RELIGION_CHOICES)
    education = filters.ChoiceFilter(lookup_expr='exact', choices=EDUCATION_CHOICES)
