from django.db.models import Q
from rest_framework import serializers

from common.exceptions import CustomValidation
from core.choices import GENDER_CHOICES
from matrimonials.choices import CONNECTION_CHOICES, EDUCATION_CHOICES, RELIGION_CHOICES
from matrimonials.models import ConnectionRequest, Conversation, MatrimonialProfile, MatrimonialProfileImage, Message


class CreateMatrimonialProfileSerializer(serializers.Serializer):
    images = serializers.ListField(child=serializers.CharField(), max_length=6)
    short_bio = serializers.CharField()
    age = serializers.IntegerField()
    gender = serializers.ChoiceField(choices=GENDER_CHOICES)
    height = serializers.CharField()
    country = serializers.CharField()
    city = serializers.CharField()
    religion = serializers.ChoiceField(choices=RELIGION_CHOICES)
    education = serializers.ChoiceField(choices=EDUCATION_CHOICES)
    profession = serializers.CharField()
    income = serializers.CharField()

    def create(self, validated_data):
        user = self.context['request'].user
        if MatrimonialProfile.objects.filter(user=user).exists():
            raise CustomValidation(
                {"message": "This user already has a matrimonial profile", "status": "failed"}
            )

        images = validated_data.pop('images')
        profile = MatrimonialProfile.objects.create(user=user, **validated_data)

        matrimonial_images = [
            MatrimonialProfileImage(matrimonial_profile=profile, image=image)
            for image in images
        ]
        MatrimonialProfileImage.objects.bulk_create(matrimonial_images)

        return profile

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if images is not None:
            # Update or create new images
            MatrimonialProfileImage.objects.filter(matrimonial_profile=instance).delete()
            matrimonial_images = [
                MatrimonialProfileImage(matrimonial_profile=instance, image=image)
                for image in images
            ]
            MatrimonialProfileImage.objects.bulk_create(matrimonial_images)

        return instance


class MatrimonialProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    images = serializers.SerializerMethodField()
    short_bio = serializers.CharField()
    religion = serializers.ChoiceField(choices=RELIGION_CHOICES)
    gender = serializers.ChoiceField(choices=GENDER_CHOICES)
    height = serializers.CharField()
    education = serializers.CharField()
    profession = serializers.CharField()
    country = serializers.CharField()
    city = serializers.CharField()
    age = serializers.IntegerField()
    income = serializers.CharField()

    @staticmethod
    def get_images(obj: MatrimonialProfile):
        return [image.image for image in obj.images.all()]


class ConnectionRequestSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    sender = serializers.UUIDField(read_only=True)
    receiver = serializers.UUIDField()
    status = serializers.ChoiceField(choices=CONNECTION_CHOICES, read_only=True)
    created = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            matrimonial_profile = MatrimonialProfile.objects.get(user=user)
        except MatrimonialProfile.DoesNotExist:
            raise CustomValidation(
                {"message": "User does not have a matrimonial profile", "status": "failed"})
        sender = matrimonial_profile
        receiver_id = validated_data.pop('receiver')
        try:
            receiver = MatrimonialProfile.objects.get(id=receiver_id)
        except MatrimonialProfile.DoesNotExist:
            raise CustomValidation(
                {"message": "Receiver matrimonial profile doesn't exist", "status": "failed"})
        validated_data['sender'] = sender
        validated_data['receiver'] = receiver
        if ConnectionRequest.objects.filter(sender=sender, receiver=receiver).exists():
            raise CustomValidation({"message": "Connection request already made", "status": "failed"})
        return ConnectionRequest.objects.create(**validated_data)

    # once the method is patch, status field is editable
    def get_fields(self):
        fields = super().get_fields()
        if self.context['request'].method == "PATCH":
            fields['status'].read_only = False
            fields['receiver'].read_only = True
        return fields

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        if instance.status == 'Rejected':
            instance.delete()
            return instance

        if instance.status == 'Accepted':
            # Create a new Conversation instance and add it to ConversationListSerializer
            conversation = Conversation.objects.create(initiator=instance.sender, receiver=instance.receiver)
            conversation_serializer = ConversationListSerializer(conversation)

            instance.delete()
            return conversation_serializer.data
        return instance


class MatrimonialProfileImageSerializer(serializers.Serializer):
    image = serializers.CharField()


class MessageSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    sender_id = serializers.SerializerMethodField()
    text = serializers.CharField(required=False)
    attachment = serializers.FileField(allow_empty_file=True, required=False, allow_null=True)
    created = serializers.DateTimeField(read_only=True)

    @staticmethod
    def get_sender_id(obj: Message):
        return obj.sender.id

    def validate(self, attrs):
        user = self.context["request"].user
        profile = user.matrimonial_profile
        try:
            MatrimonialProfile.objects.get(id=profile.id)
        except MatrimonialProfile.DoesNotExist:
            return CustomValidation(
                {"message": "Sender matrimonial profile doesn't exist", "status": "failed"})
        return attrs


def validate_profiles(attrs):
    initiator = attrs.get('initiator')
    receiver = attrs.get('receiver')

    try:
        MatrimonialProfile.objects.get(id=initiator)
        MatrimonialProfile.objects.get(id=receiver)
    except MatrimonialProfile.DoesNotExist:
        return CustomValidation(
            {"message": "Initiator or receiver matrimonial profile doesn't exist", "status": "failed"})

    return attrs


class ConversationListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    receiving_user = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    def get_avatar(self, obj: Conversation):
        current_user = self.context["request"].user
        if current_user == obj.initiator:
            image = obj.receiver.images.first()
            return MatrimonialProfileImageSerializer(image).data or None
        return MatrimonialProfileImageSerializer(obj.initiator.images.first()).data or None

    def get_receiving_user(self, obj: Conversation):
        current_user = self.context["request"].user
        if current_user == obj.initiator:
            return {"full_name": obj.receiver.user.full_name, "id": obj.receiver.id}
        else:
            return {"full_name": obj.initiator.user.full_name, "id": obj.initiator.id}

    @staticmethod
    def get_last_message(obj: Conversation):
        message = obj.messages.order_by('-created').first()
        if message is None:
            return ''
        return MessageSerializer(message).data

    def validate(self, attrs):
        attrs = validate_profiles(attrs)
        return attrs


class ConversationCreateSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    receiver = serializers.UUIDField(write_only=True)
    receiving_user = serializers.SerializerMethodField()
    receiver_profile_image = serializers.SerializerMethodField()
    text = serializers.CharField()
    attachment = serializers.FileField(required=False)

    def create(self, validated_data):
        user = self.context['request'].user
        initiator = user.matrimonial_profile
        receiver_id = validated_data.get('receiver')
        text = validated_data.get('text')
        attachment = validated_data.get('attachment')

        try:
            receiver = MatrimonialProfile.objects.get(id=receiver_id)
        except MatrimonialProfile.DoesNotExist:
            raise CustomValidation({"message": "Receiver matrimonial profile doesn't exist", "status": "failed"})

        if receiver == initiator:
            raise CustomValidation({"message": "Initiator cannot chat with him/herself", "status": "failed"})

        # Check if a conversation already exists between the initiator and receiver
        existing_conversation = Conversation.objects.filter(
            (Q(initiator=initiator) & Q(receiver=receiver)) |
            (Q(initiator=receiver) & Q(receiver=initiator))
        ).first()

        if existing_conversation:
            # Create and add a message to the existing chat
            if text or attachment:
                Message.objects.create(sender=initiator, conversation=existing_conversation, text=text,
                                       attachment=attachment)
            return existing_conversation
        else:
            conversation = Conversation.objects.create(initiator=initiator, receiver=receiver)
            if text or attachment:
                Message.objects.create(sender=initiator, conversation=conversation, text=text, attachment=attachment)
            return conversation


class ConversationSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    receiver = serializers.UUIDField(write_only=True)
    receiving_user = serializers.SerializerMethodField()
    receiver_profile_image = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True)

    @staticmethod
    def get_receiver_profile_image(obj: Conversation):
        receiver_image = obj.receiver.images.first()
        if receiver_image:
            serializer = MatrimonialProfileImageSerializer(receiver_image)
            return serializer.data
        return None

    def get_receiving_user(self, obj: Conversation):
        current_user = self.context["request"].user
        if current_user == obj.initiator:
            return {"full_name": obj.receiver.user.full_name, "id": obj.receiver.id}
        else:
            return {"full_name": obj.initiator.user.full_name, "id": obj.initiator.id}
