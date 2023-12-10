from urllib.parse import urlencode

from django.contrib import admin
from django.contrib.admin import TabularInline, StackedInline
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from ads.models import Ad, AdCategory, AdImage, AdReport, AdSubCategory


# Register your models here.

class AdImageAdmin(TabularInline):
    model = AdImage
    extra = 2
    max_num = 3


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    inlines = (AdImageAdmin,)
    list_display = ('name', 'ad_creator', 'price', 'category', 'location', 'featured', 'is_approved')
    list_editable = ('featured', 'is_approved',)
    list_filter = ('name', 'price', 'category', 'location')
    list_per_page = 20
    ordering = ('name', 'category', 'ad_creator')
    search_fields = ('title', 'category__title')


class AdSubCategoryAdmin(TabularInline):
    model = AdSubCategory
    extra = 1


@admin.register(AdCategory)
class AdCategoryAdmin(admin.ModelAdmin):
    inlines = (AdSubCategoryAdmin,)
    list_display = ('title', 'ads_count', 'sub_categories_count',)
    list_filter = ('title',)
    list_per_page = 20
    ordering = ('title',)
    search_fields = ('title',)

    @admin.display(ordering="ads_count")
    def ads_count(self, category):
        url = (reverse("admin:ads_ad_changelist")
               + "?"
               + urlencode({"category__id": str(category.id)})
               )

        return format_html('<a href="{}">{} Ads</a>', url, category.ads_count)

    @admin.display(ordering="sub_categories_count")
    def sub_categories_count(self, obj: AdCategory):
        return obj.sub_categories_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request).annotate(
                ads_count=Count("ads"),
                sub_categories_count=Count("sub_categories")
        )
        return queryset


@admin.register(AdReport)
class AdReport(admin.ModelAdmin):
    list_display = ('ad_name', 'reporter_email', 'report')
    list_per_page = 30

    def has_add_permission(self, request):
        return False

    @staticmethod
    def ad_name(obj: AdReport):
        return obj.ad.name

    @staticmethod
    def reporter_email(obj: AdReport):
        return obj.reporter.email

    @staticmethod
    def report(obj: AdReport):
        max_length = 50  # Set the desired maximum length for the title
        if len(obj.text) > max_length:
            return obj.text[:max_length] + '...'
        return obj.text
