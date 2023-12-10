from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ads.choices import STATUS_ACTIVE
from ads.filters import AdFilter
from ads.mixins import AdsByCategoryMixin
from ads.models import Ad, AdCategory, Chat, FavouriteAd
from ads.serializers import AdCategorySerializer, AdSerializer, ChatListSerializer, ChatSerializer, CreateAdSerializer, \
    ReportAdSerializer, ChatCreateSerializer

User = get_user_model()


# Create your views here.

class RetrieveAllApprovedActiveAdsView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get all ads",
        description=
        """
        Retrieve list of all ads approved and made active by client.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Ad successfully fetched",
                response=AdSerializer(many=True),
            ),
        }
    )
    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        all_ads = Ad.objects.filter(is_approved=True, status=STATUS_ACTIVE)
        data = [
            {
                "id": ad.id,
                "name": ad.name,
                "ad_owner_id": ad.ad_creator.id,
                "ad_owner_image": ad.ad_creator.profile.avatar,
                "ad_owner_name": ad.ad_creator.full_name,
                "ad_owner_phone_number": ad.ad_creator.phone_number,
                "description": ad.description,
                "price": ad.price,
                "location": ad.location,
                "category": {
                    "id": ad.category.id,
                    "title": ad.category.title
                },
                "sub_category": "" if ad.sub_category is None else {
                    "id": ad.sub_category.id,
                    "title": ad.sub_category.title,
                },
                "images": [image.image for image in ad.images.all()],
                "featured": ad.featured,
                "is_approved": ad.is_approved,
                "status": ad.status,
            }
            for ad in all_ads
        ]

        return Response(
            {"message": "Ads retrieved successfully", "data": data, "status": "success"},
            status=status.HTTP_200_OK)


class AdsCategoryView(AdsByCategoryMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdCategorySerializer

    @extend_schema(
        summary="Ads and Categories",
        description=
        """
        Get all active ads and categories including featured ads.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Ad successfully fetched",
                response=AdSerializer(many=True)
            ),
        }
    )
    def get(self, request):
        ad_categories = AdCategory.objects.all()
        serializer = AdCategorySerializer(ad_categories, many=True)
        featured_ads = Ad.objects.select_related('category').filter(featured=True, is_approved=True,
                                                                    status=STATUS_ACTIVE)
        serialized_featured_ads = AdSerializer(featured_ads, many=True)
        count_featured_ads = featured_ads.count()
        all_ads_by_category = []
        for category in ad_categories:
            ads = self.get_ads_by_category(category.id)
            num_ads = ads.count()
            all_ads_by_category.append({
                "category": category.id,
                "title": category.title,
                "num_ads": num_ads,
                "ads": AdSerializer(ads, many=True).data
            })
        data = {
            "ad_categories": serializer.data,
            "featured_ads": {
                "ads": serialized_featured_ads.data,
                "count_featured_ads": count_featured_ads,
            },
            "all_ads_by_category": all_ads_by_category,
        }
        return Response({"message": "Fetched successfully", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)


class RetrieveAllCategoriesAndSubcategories(GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = AdCategory.objects.all()

    @extend_schema(
        summary="Categories and Sub-Categories",
        description=
        """
        Get all categories and sub-categories.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Ad successfully fetched",
                response=AdCategorySerializer(many=True)
            ),
        }
    )
    def get(self, request):
        categories = self.get_queryset()
        serialized_data = [
            {
                "title": category.title,
                "sub_category": [
                    {
                        "title": sub_category.title
                    }
                    for sub_category in category.sub_categories.all()
                ],
                "image": category.image,
            }
            for category in categories
        ]
        return Response({"message": "Fetched successfully", "data": serialized_data, "status": "success"},
                        status=status.HTTP_200_OK)


class RetrieveAdView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Ad Detail",
        description=
        """
        Get the details of a specific Ad.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Ad successfully fetched",
                response=AdSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="This ad does not exist, try again",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Ad ID is required",
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        ad_id = self.kwargs.get('ad_id')
        if ad_id is None:
            return Response({"message": "Ad ID is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            ad = Ad.objects.get(id=ad_id)
        except Ad.DoesNotExist:
            return Response({"message": "Ad with this id does not exist", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        data = {
            "id": ad.id,
            "ad_creator": ad.ad_creator.full_name,
            "name": ad.name,
            "description": ad.description,
            "price": ad.price,
            "location": ad.location,
            "images": [image.image for image in ad.images.all()],
            "featured": ad.featured,
            "is_approved": ad.is_approved,
            "status": ad.status,
        }
        return Response({"message": "Ad fetched successfully", "data": data}, status=status.HTTP_200_OK)


class FilteredAdsListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdSerializer
    filterset_class = AdFilter
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'description', 'category__title', 'price']
    queryset = Ad.objects.filter(is_approved=True, status=STATUS_ACTIVE)

    @extend_schema(
        summary="Filtered Ads List",
        description=
        """
        This endpoint retrieves a list of filtered ads.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Ads filtered successfully.",
                response=AdSerializer(many=True)
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True)
        return Response({"message": "Ads filtered successfully", "data": serializer.data, "status": "success"},
                        status.HTTP_200_OK)


class CreateAdsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateAdSerializer

    @extend_schema(
        summary="Create a ad",
        description=
        """
        This endpoint allows an authenticated user to create an ad.
        """,
        request=CreateAdSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Ad created successfully",
                response=AdSerializer,
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request. Maximum number of allowed images exceeded.",
            ),
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        created_ad = serializer.save()
        # Serialize the Ad instance with associated images
        serialized_data = AdSerializer(created_ad).data
        return Response({"message": "Ad created successfully", "data": serialized_data, "status": "success"},
                        status.HTTP_201_CREATED)


class RetrieveUserAdsView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get all ads relate to user",
        description=
        """
        Get all ads related to the authenticated user.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Ad successfully fetched",
                response=AdSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="User has not created any ads",
            ),
        }
    )
    def get(self, request):
        creator = self.request.user
        ads = Ad.objects.filter(ad_creator=creator)
        if not ads.exists():
            return Response({"message": "User has not created any ads", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        all_user_ads = [
            {
                "ad_id": ad.id,
                "created": ad.created,
                "name": ad.name,
                "price": ad.price,
                "image": [image.image for image in ad.images.all()],
                "is_approved": ad.is_approved,
                "status": ad.status
            }.copy()
            for ad in ads
        ]

        return Response({"message": "All user ads fetched successfully", "data": all_user_ads, "status": "success"},
                        status=status.HTTP_200_OK)


class UpdateUserAdView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateAdSerializer

    @extend_schema(
        summary="Update Ad",
        description=
        """
        Update user ad.
        """,
        request=CreateAdSerializer,
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Ad successfully updated",
                response=AdSerializer
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="This ad does not exist, try again",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Ad ID is required",
            ),
        }
    )
    def patch(self, request, *args, **kwargs):
        creator = self.request.user
        ad_id = self.kwargs.get('ad_id')
        if ad_id is None:
            return Response({"message": "Ad ID is required", "status": "success"},
                            status=status.HTTP_400_BAD_REQUEST)
        ad = Ad.objects.filter(ad_creator=creator, id=ad_id)
        if ad.exists():
            ad = ad.get()
            serializer = self.serializer_class(ad, data=self.request.data, partial=True, context={"request": request})
            serializer.is_valid(raise_exception=True)
            updated_data = serializer.save()
            serialized_data = AdSerializer(updated_data).data
            return Response({"message": "Ad updated successfully", "data": serialized_data, "status": "success"},
                            status=status.HTTP_202_ACCEPTED)
        else:
            return Response({"message": "Ad with this id does not exist", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)


class DeleteUserAdView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Remove Ad",
        description=
        """
        Remove ad from ads list.
        """,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Ad successfully removed",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="This ad does not exist, try again",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Ad ID is required",
            ),
        }
    )
    def delete(self, request, *args, **kwargs):
        ad_id = self.kwargs.get('ad_id')
        if ad_id is None:
            return Response({"message": "Ad ID is required", "status": "success"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            ad = Ad.objects.get(id=ad_id)
        except Ad.DoesNotExist:
            return Response({"message": "Ad with this id does not exist", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        ad.delete()
        return Response({"message": "Ad removed successfully", "status": "success"}, status=status.HTTP_204_NO_CONTENT)


class FavouriteAdView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Add ad to favorites",
        description=
        """
        This endpoint allows an authenticated user to add an ad to their favorites list.
        """,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Ad added to favorites.",
                response=AdSerializer
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or missing ad ID.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Ad not found.",
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        customer = self.request.user
        ad_id = self.kwargs.get("ad_id")
        if not ad_id:
            return Response({"message": "Ad id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            ad = Ad.objects.get(id=ad_id)
        except Ad.DoesNotExist:
            return Response({"message": "Invalid ad id", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)

        favourite, created = FavouriteAd.objects.get_or_create(customer=customer, ad=ad)
        if created:
            serialized_ad = AdSerializer(ad).data
            return Response({"message": "Ad added to favourites", "data": serialized_ad, "status": "success"},
                            status=status.HTTP_201_CREATED)
        else:
            serialized_ad = AdSerializer(favourite.ad).data
            return Response({"message": "Ad already in favourites", "data": serialized_ad, "status": "success"},
                            status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete an item in favorites",
        description=
        """
        This endpoint allows an authenticated user to remove an ad in their favorites list.
        """,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Ad removed successfully",
                response=AdSerializer
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or missing ad ID.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Ad not found.",
            ),
        }
    )
    def delete(self, request, *args, **kwargs):
        customer = self.request.user
        ad_id = self.kwargs.get("ad_id")
        if not ad_id:
            return Response({"message": "Ad id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            ad = Ad.objects.get(id=ad_id)
        except Ad.DoesNotExist:
            return Response({"message": "Invalid ad id", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)

        favourite = FavouriteAd.objects.get(customer=customer, ad=ad)
        favourite.delete()
        return Response({"message": "Ad removed successfully", "status": "success"}, status=status.HTTP_204_NO_CONTENT)


class FavouriteAdListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Retrieves all favorite ads",
        description=
        """
        This endpoint allows an authenticated user to retrieve their favorite ads list.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="All favorite products fetched.",
                response=AdSerializer(many=True)
            ),
        }
    )
    def get(self, request):
        customer = self.request.user
        favourite_ads = FavouriteAd.objects.select_related('ad').filter(customer=customer)
        if not favourite_ads.exists():
            return Response({"message": "Customer has no favourite ads", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serialized_data = [
            {
                "id": a.ad.id,
                "name": a.ad.name,
                "ad_owner_id": a.customer.id,
                "ad_owner_image": a.customer.profile.avatar,
                "ad_owner_name": a.customer.full_name,
                "ad_owner_phone_number": a.customer.phone_number,
                "description": a.ad.description,
                "price": a.ad.price,
                "location": a.ad.location,
                "category": {
                    "id": a.ad.category.id,
                    "title": a.ad.category.title
                },
                "sub_category": "" if a.ad.sub_category is None else {
                    "id": a.ad.sub_category.id,
                    "title": a.ad.sub_category.title,
                },
                "images": [image.image for image in a.ad.images.all()],
                "featured": a.ad.featured,
                "is_approved": a.ad.is_approved,
                "status": a.ad.status,
            }
            for a in favourite_ads
        ]
        return Response({"message": "All favorite products fetched", "data": serialized_data, "status": "success"},
                        status=status.HTTP_200_OK)


class ReportAdView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReportAdSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Report an ad",
        description=
        """
        This endpoint allows an authenticated user to report an ad.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Ad reported successfully.",
                response=ReportAdSerializer
            ),
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Ad reported successfully", "status": "success"}, status=status.HTTP_200_OK)


class ChatListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatListSerializer

    @extend_schema(
        summary="Retrieve Chat List",
        description=
        """
        This endpoint retrieve chat list.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Chat list fetched successfully",
                response=ChatListSerializer(many=True)
            ),
        },
    )
    def get(self, request):
        user = self.request.user
        conversation_list = Chat.objects.filter(Q(initiator=user) | Q(receiver=user))

        # Create a dictionary to group chats by user
        chat_groups = defaultdict(list)
        for chat in conversation_list:
            other_user = chat.receiver if chat.initiator == user else chat.initiator
            chat_groups[other_user].append(chat)

        # Extract the latest message from each chat group
        chats = []
        for user, user_chats in chat_groups.items():
            latest_messages = [chat.messages.order_by('-created').first() for chat in user_chats]
            latest_chat = max(latest_messages, key=lambda message: message.created)
            chats.append(latest_chat.chat)  # Assuming you have a 'chat' field in your Message model.

        # Serialize the chat list
        serializer = self.serializer_class(instance=chats, many=True, context={"request": request})

        return Response(
            {"message": "Chat list fetched successfully", "data": serializer.data, "status": "success"},
            status=status.HTTP_200_OK
        )


class RetrieveChatView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSerializer

    @extend_schema(
        summary="Retrieve a chat",
        description=
        """
        This endpoint retrieve a chat.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Chat fetched successfully",
                response=ChatSerializer
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Chat does not exist",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        chat_id = self.kwargs.get('chat_id')
        chat = Chat.objects.filter(id=chat_id)
        if not chat.exists():
            return Response({"message": "Chat does not exist", "status": "success"},
                            status=status.HTTP_404_NOT_FOUND)
        else:
            serializer = self.serializer_class(instance=chat.get(), context={"request": request})
            return Response(
                {"message": "Chat fetched successfully", "data": serializer.data, "status": "success"},
                status=status.HTTP_200_OK)


class CreateChatView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatCreateSerializer

    @extend_schema(
        summary="Create a chat or send message",
        description=
        """
        This endpoint creates a chat and can be used to send a message.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Message sent successfully",
                response=ChatSerializer,
            ),
        },
    )
    def post(self, request):
        with transaction.atomic():
            serializer = self.get_serializer(data=self.request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)

            # Create the chat
            chat = serializer.save()

            data = {
                "id": chat.id,
                "receiving_user": {
                    "id": chat.receiver.id,
                    "full_name": chat.receiver.full_name,
                },
                "receiver_profile_image": chat.receiver.profile.avatar,
                "message": chat.messages.first().text,
                "attachment": chat.messages.first().attachment or ""
            }
            return Response({"message": "Message sent successfully", "data": data, "status": "success"},
                            status=status.HTTP_201_CREATED)


class DeleteChatRoomView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Delete a chat",
        description=
        """
        This endpoint deletes a chat.
        """,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Chat deleted successfully",
                response=ChatSerializer,
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        chat_id = self.kwargs.get('chat_id')
        if chat_id is None:
            return Response({"message": "Chat ID is required", "status": "success"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({"message": "Chat with this id does not exist", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        chat.delete()
        return Response({"message": "Chat deleted successfully", "status": "success"},
                        status=status.HTTP_204_NO_CONTENT)
