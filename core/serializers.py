import re

from django.core.validators import validate_email
from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from common.exceptions import CustomValidation
from core.models import Feedback, User, UserReport


class VerifyPasswordOTPSerializer(serializers.Serializer):
    email = serializers.CharField()
    code = serializers.IntegerField()

    def validate(self, attrs):
        code = attrs.get('code')

        if not code:
            raise CustomValidation({"message": "Code is required", "status": "failed"})

        if not re.match("^[0-9]{4}$", str(code)):
            raise CustomValidation({"message": "Code must be 4-digit number", "status": "failed"})

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=50, min_length=6, write_only=True)
    confirm_pass = serializers.CharField(max_length=50, min_length=6, write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        confirm = attrs.get('confirm_pass')

        if confirm != password:
            raise CustomValidation({"message": "Passwords do not match", "status": "failed"})

        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(max_length=150, min_length=6, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            validate_email(email)
        except Exception:
            raise CustomValidation({"message": "Invalid email format", "status": "failed"})

        return attrs


class ProfileSerializer(serializers.Serializer):
    full_name = serializers.CharField(source="user.full_name")
    email = serializers.CharField(source="user.email")
    description = serializers.CharField()
    avatar = serializers.CharField()
    country = serializers.CharField(source="user.country")
    phone_number = serializers.CharField(source="user.phone_number")

    @staticmethod
    def validate_phone_number(value):
        phone_number = value
        if not phone_number.startswith('+'):
            raise CustomValidation({"message": "Phone number must start with a plus sign (+)", "status": "failed"})
        if not phone_number[1:].isdigit():
            raise CustomValidation(
                {"message": "Phone number must only contain digits after the plus sign (+)", "status": "failed"})
        return value


class RegisterSerializer(serializers.Serializer):
    email = serializers.CharField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    country = serializers.CharField()
    password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        full_name = attrs.get('full_name')
        phone_number = attrs.get('phone_number')

        if User.objects.filter(email=email).exists():
            raise CustomValidation({"message": "User with this email address already exists", "status": "failed"})

        try:
            validate_email(email)
        except Exception:
            raise CustomValidation({"message": "Invalid email format", "status": "failed"})

        if not full_name:
            raise CustomValidation({"message": "full name is required", "status": "failed"})

        if not phone_number.startswith('+'):
            raise CustomValidation({"message": "Phone number must start with a plus sign (+)", "status": "failed"})
        if not phone_number[1:].isdigit():
            raise CustomValidation(
                {"message": "Phone number must only contain digits after the plus sign (+)", "status": "failed"})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RequestNewPasswordCodeSerializer(serializers.Serializer):
    email = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            validate_email(email)
        except Exception:
            raise CustomValidation({"message": "Invalid email format", "status": "failed"})
        return attrs


class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            validate_email(email)
        except Exception:
            raise CustomValidation({"message": "Invalid email format", "status": "failed"})
        return attrs


class UpdateProfileSerializer(serializers.Serializer):
    full_name = serializers.CharField(source="user.full_name")
    email = serializers.CharField(source="user.email", read_only=True)
    avatar = serializers.CharField()
    description = serializers.CharField()
    country = serializers.CharField(source="user.country")
    language = serializers.CharField()
    phone_number = serializers.CharField(source="user.phone_number")

    @staticmethod
    def validate_phone_number(value):
        phone_number = value
        if not phone_number.startswith('+'):
            raise CustomValidation({"message": "Phone number must start with a plus sign (+)", "status": "failed"})
        if not phone_number[1:].isdigit():
            raise CustomValidation(
                {"message": "Phone number must only contain digits after the plus sign (+)", "status": "failed"})
        return value

    def update(self, instance, validated_data):
        # Update User model fields
        user_data = validated_data.pop('user', {})
        for key, value in user_data.items():
            setattr(instance.user, key, value)

        # Update Profile model fields
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.user.save()
        instance.save()

        return instance


class VerifyEmailSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    email = serializers.CharField()

    def validate(self, attrs):
        code = attrs.get('code')
        email = attrs.get('email')

        if not code:
            raise CustomValidation({"message": "Code is required", "status": "failed"})

        if not re.match("^[0-9]{4}$", str(code)):
            raise CustomValidation({"message": "Code must be a 4-digit number", "status": "failed"})

        try:
            validate_email(email)
        except CustomValidation:
            raise CustomValidation({"message": "Invalid email format", "status": "failed"})

        return attrs


class FeedbackSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    comment = serializers.CharField()

    def create(self, validated_data):
        user = self.context['request'].user
        return Feedback.objects.create(user=user, **validated_data)


class ReportUserSerializer(serializers.Serializer):
    offender_id = serializers.UUIDField()
    text = serializers.CharField()

    def create(self, validated_data):
        reporter = self.context['request'].user
        offender_id = validated_data.get('offender_id')

        try:
            offender = User.objects.get(id=offender_id)
        except User.DoesNotExist:
            raise CustomValidation({"message": "User does not exist", "status": "failed"})

        return UserReport.objects.create(reporter=reporter, offender=offender, **validated_data)
