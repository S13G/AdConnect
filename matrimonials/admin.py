from django.contrib import admin
from django.contrib.admin import TabularInline

from matrimonials.models import MatrimonialProfile, MatrimonialProfileImage


# Register your models here.

class MatrimonialProfileImageAdmin(TabularInline):
    model = MatrimonialProfileImage
    extra = 1
    max_num = 6


@admin.register(MatrimonialProfile)
class MatrimonialProfileAdmin(admin.ModelAdmin):
    inlines = (MatrimonialProfileImageAdmin,)
    list_display = ('full_name', 'gender', 'country', 'city', 'religion', 'income',)
    list_filter = ('gender', 'country', 'city', 'religion', 'profession',)
    list_per_page = 20
    ordering = ('gender', 'religion',)
    search_fields = ('full_name', 'country',)
