from django.contrib.auth import get_user_model
from rest_framework import serializers

from ads.choices import STATUS_CHOICES
from ads.models import Ad, AdCategory, AdImage, AdReport, AdSubCategory, Chat, Message
from common.exceptions import CustomValidation

User = get_user_model()


class AdCategorySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    image = serializers.ImageField()


class AdSubCategorySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    category = AdCategorySerializer
    title = serializers.CharField()


class AdSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.CharField()
    location = serializers.CharField()
    category = AdCategorySerializer
    sub_category = AdSubCategorySerializer
    featured = serializers.BooleanField()
    images = serializers.SerializerMethodField()
    is_approved = serializers.BooleanField()
    status = serializers.ChoiceField(choices=STATUS_CHOICES)

    @staticmethod
    def get_images(obj: Ad):
        images = [image.image for image in obj.images.all()]
        return images


class CreateAdSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.CharField()
    location = serializers.CharField()
    category = serializers.CharField()
    sub_category = serializers.CharField()
    images = serializers.ListField(child=serializers.URLField(), required=False, max_length=3)
    featured = serializers.BooleanField()
    is_approved = serializers.BooleanField()
    status = serializers.ChoiceField(choices=STATUS_CHOICES)

    def get_fields(self):
        fields = super().get_fields()
        if self.context['request'].method == "PATCH":
            fields['featured'].read_only = True
            fields['is_approved'].read_only = True
        else:
            fields['status'].read_only = True
            fields['featured'].read_only = True
            fields['is_approved'].read_only = True
        return fields

    @staticmethod
    def validate_name(value):
        if Ad.objects.filter(name=value).exists():
            raise CustomValidation({"message": "An ad with this name already exists.", "status": "failed"})
        return value

    def create(self, validated_data):
        creator = self.context['request'].user
        category_name = validated_data.pop('category')
        sub_category_name = validated_data.pop('sub_category')

        try:
            category = AdCategory.objects.get(title__icontains=category_name)
        except AdCategory.DoesNotExist:
            raise CustomValidation({"message": "Category does not exist", "status": "failed"})

        if sub_category_name is not None:
            try:
                sub_category = category.sub_categories.get(title__icontains=sub_category_name)
            except AdSubCategory.DoesNotExist:
                raise CustomValidation({"message": "Sub Category does not exist", "status": "failed"})
        else:
            sub_category = None

        images = validated_data.pop('images', [])  # Get the images list or an empty list if not provided

        if len(images) > 3:
            raise CustomValidation({"message": "The maximum number of allowed images is 3", "status": "failed"})

        # Create the Ad instance without saving it to the database
        ad = Ad.objects.create(ad_creator=creator, category=category, sub_category=sub_category, **validated_data)

        # Create AdImage instances and associate them with the Ad instance using set()
        ad_images = [AdImage(ad=ad, image=image) for image in images]
        AdImage.objects.bulk_create(ad_images)

        # Finally, save the Ad instance to the database and return it
        ad.save()
        return ad

    def update(self, instance, validated_data):
        category_name = self.validated_data.pop('category', None)
        sub_category_name = self.validated_data.pop('sub_category', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if category_name is not None:
            try:
                category = AdCategory.objects.get(title__icontains=category_name)
            except AdCategory.DoesNotExist:
                raise CustomValidation({"message": "Category does not exist", "status": "failed"})

            if sub_category_name is not None:
                try:
                    sub_category = category.sub_categories.get(title__icontains=sub_category_name)
                except AdSubCategory.DoesNotExist:
                    raise CustomValidation({"message": "Sub Category does not exist", "status": "failed"})
            else:
                raise CustomValidation({"message": "You are trying to change the category without selecting a sub",
                                        "status": "failed"})

            instance.category = category
            instance.sub_category = sub_category
        instance.save()
        return instance


class ReportAdSerializer(serializers.Serializer):
    ad = serializers.UUIDField()
    text = serializers.CharField()

    def create(self, validated_data):
        reporter = self.context['request'].user
        ad_id = validated_data.pop('ad')

        try:
            ad = Ad.objects.get(id=ad_id)
        except Ad.DoesNotExist:
            raise CustomValidation({"message": "Ad does not exist", "status": "failed"})

        return AdReport.objects.create(ad=ad, reporter=reporter, **validated_data)


class MessageSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    sender = serializers.SerializerMethodField()
    text = serializers.CharField(required=False)
    attachment = serializers.FileField(allow_empty_file=True, required=False, allow_null=True)
    created = serializers.DateTimeField(read_only=True)

    @staticmethod
    def get_sender(obj: Message):
        return obj.sender.id


def validate_users(attrs):
    initiator = attrs.get('initiator')
    receiver = attrs.get('receiver')

    try:
        User.objects.get(id=initiator)
        User.objects.get(id=receiver)
    except User.DoesNotExist:
        return CustomValidation(
            {"message": "Initiator or receiver doesn't exist", "status": "failed"})

    return attrs


class ChatListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    ad_id = serializers.SerializerMethodField()
    ad_title = serializers.SerializerMethodField()
    ad_image = serializers.SerializerMethodField()
    receiving_user = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    @staticmethod
    def get_ad_id(obj: Chat):
        return obj.ad.id

    # get profile image
    def get_avatar(self, obj: Chat):
        current_user = self.context["request"].user
        if current_user == obj.initiator:
            return obj.receiver.profile.avatar
        return obj.initiator.profile.avatar

    def get_receiving_user(self, obj: Chat):
        current_user = self.context["request"].user
        if current_user == obj.initiator:
            return {"full_name": obj.receiver.full_name, "id": obj.receiver.id}
        else:
            return {"full_name": obj.initiator.full_name, "id": obj.initiator.id}

    @staticmethod
    def get_last_message(obj: Chat):
        message = obj.messages.order_by('-created').first()
        if message is None:
            return ''
        return MessageSerializer(message).data

    @staticmethod
    def get_ad_title(obj: Chat):
        return obj.ad.name

    @staticmethod
    def get_ad_image(obj: Chat):
        return obj.ad.images.first().image if obj.ad.images.first() else None

    def validate(self, attrs):
        attrs = validate_users(attrs)
        return attrs


class ChatCreateSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    ad_id = serializers.UUIDField(write_only=True)
    receiver = serializers.UUIDField(write_only=True)
    receiving_user = serializers.SerializerMethodField()
    receiver_profile_image = serializers.SerializerMethodField()
    text = serializers.CharField()
    attachment = serializers.FileField(required=False)

    def create(self, validated_data):
        ad_id = validated_data.get('ad_id')
        initiator = self.context['request'].user
        receiver = validated_data.get('receiver')
        text = validated_data.get('text')
        attachment = validated_data.get('attachment')

        try:
            ad = Ad.objects.get(id=ad_id)
        except Ad.DoesNotExist:
            raise CustomValidation({"message": "Ad does not exist", "status": "failed"})

        try:
            receiver = User.objects.get(id=receiver)
        except User.DoesNotExist:
            raise CustomValidation({"message": "Receiver doesn't exist", "status": "failed"})

        if receiver == initiator:
            raise CustomValidation({"message": "Initiator cannot chat with him/herself", "status": "failed"})

        # Check if a conversation already exists between the ad and receiver
        existing_chat = Chat.objects.filter(ad=ad, receiver=receiver).first()

        if existing_chat:
            # Create and add a message to the existing chat
            if text or attachment:
                Message.objects.create(sender=initiator, chat=existing_chat, text=text, attachment=attachment)
            return existing_chat
        else:
            chat = Chat.objects.create(ad=ad, initiator=initiator, receiver=receiver)
            if text or attachment:
                Message.objects.create(sender=initiator, chat=chat, text=text, attachment=attachment)
            return chat


class ChatSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    ad_id = serializers.UUIDField(write_only=True)
    receiver = serializers.UUIDField(write_only=True)
    receiving_user = serializers.SerializerMethodField()
    receiver_profile_image = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True)

    @staticmethod
    def get_receiver_profile_image(obj: Chat):
        return obj.initiator.profile.avatar

    def get_receiving_user(self, obj: Chat):
        current_user = self.context["request"].user
        if current_user == obj.initiator:
            return {"full_name": obj.receiver.full_name, "id": obj.receiver.id}
        else:
            return {"full_name": obj.initiator.full_name, "id": obj.initiator.id}
