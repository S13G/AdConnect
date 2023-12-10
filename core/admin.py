from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.forms import CustomUserChangeForm, CustomUserCreationForm
from core.models import Feedback, Profile, User, UserReport


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        "email",
        "full_name",
        "phone_number",
        "country",
        "is_staff",
        "is_active",
        "is_verified"
    )
    list_filter = (
        "email",
        "phone_number",
        "full_name",
        "is_staff",
        "is_active",
    )
    list_per_page = 30
    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "email",
                    "full_name",
                    "phone_number",
                    "country",
                    "password",
                    "is_verified",
                )
            },
        ),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "groups", "user_permissions")},
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email_address",
        "phone_number"
    )
    list_per_page = 30
    ordering = ("user__email",)
    search_fields = ("email_address",)

    @staticmethod
    def full_name(obj: Profile):
        return obj.user.full_name

    @staticmethod
    def email_address(obj: Profile):
        return obj.user.email

    @staticmethod
    def phone_number(obj: Profile):
        return obj.user.phone_number


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "feedback_text")
    list_per_page = 30
    ordering = ("user__full_name",)

    # Exclude the "add" permission for this model
    def has_add_permission(self, request):
        return False

    @staticmethod
    def full_name(obj: Feedback):
        return obj.user.full_name

    @staticmethod
    def feedback_text(obj: Feedback):
        max_length = 50  # Set the desired maximum length for the title
        if len(obj.comment) > max_length:
            return obj.comment[:max_length] + '...'
        return obj.comment


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ("reporter_email", "offender_email", "report")
    list_per_page = 30

    @staticmethod
    def reporter_email(obj: UserReport):
        return obj.reporter.email

    @staticmethod
    def offender_email(obj: UserReport):
        return obj.offender.email

    @staticmethod
    def report(obj: UserReport):
        max_length = 50  # Set the desired maximum length for the title
        if len(obj.text) > max_length:
            return obj.text[:max_length] + '...'
        return obj.text
