from collections import defaultdict
from operator import attrgetter

from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from matrimonials.filters import MatrimonialFilter
from matrimonials.models import BookmarkedProfile, ConnectionRequest, Conversation, FavouriteProfile, \
    MatrimonialProfile
from matrimonials.serializers import ConnectionRequestSerializer, ConversationListSerializer, \
    ConversationSerializer, CreateMatrimonialProfileSerializer, MatrimonialProfileSerializer, \
    ConversationCreateSerializer


class RetrieveAllMatrimonialProfilesView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Get all matrimonial profiles",
        description=
        """
        This endpoint allows an authenticated user to retrieve all matrimonial profile.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="All Matrimonial Profile retrieved successfully",
                response=MatrimonialProfileSerializer
            ),
        }
    )
    def get(self, request):
        all_matrimonial_profiles = MatrimonialProfile.objects.all().exclude(user=self.request.user)
        data = [
            {
                "id": profile.id,
                "full_name": profile.full_name,
                "short_bio": profile.short_bio,
                "gender": profile.gender,
                "religion": profile.religion,
                "country": profile.country,
                "city": profile.city,
                "education": profile.education,
                "profession": profile.profession,
                "income": profile.income,
                "age": profile.age,
                "height": profile.height,
                "images": [image.image for image in profile.images.all()]
            }.copy()
            for profile in all_matrimonial_profiles
        ]
        return Response(
            {"message": "All matrimonial profiles fetched", "data": data, "status": "success"},
            status=status.HTTP_200_OK)


class RetrieveCreateUpdateMatrimonialProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateMatrimonialProfileSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Get logged in user matrimonial profile",
        description=
        """
        This endpoint allows an authenticated user to retrieve his/her matrimonial profile.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Matrimonial Profile retrieved successfully",
                response=MatrimonialProfileSerializer
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="User does not have matrimonial profile.",
            ),
        }
    )
    def get(self, request):
        user = self.request.user
        try:
            user_matrimonial_profile = MatrimonialProfile.objects.get(user=user)
        except MatrimonialProfile.DoesNotExist:
            return Response({"message": "User does not have matrimonial profile", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serialized_data = MatrimonialProfileSerializer(user_matrimonial_profile).data
        return Response(
            {"message": "Matrimonial profile fetched successfully", "data": serialized_data, "status": "success"},
            status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update matrimonial profile for logged in user",
        description=
        """
        This endpoint allows an authenticated user to update a matrimonial profile for him/herself.
        """,
        request=CreateMatrimonialProfileSerializer,
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Matrimonial Profile updated successfully",
                response=MatrimonialProfileSerializer
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request. Maximum number of allowed images exceeded.",
            ),
        }
    )
    def patch(self, request):
        user = self.request.user

        try:
            user_matrimonial_profile = MatrimonialProfile.objects.get(user=user)
        except MatrimonialProfile.DoesNotExist:
            return Response({"message": "User does not have matrimonial profile", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(user_matrimonial_profile, data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        saved_serializer = serializer.save()
        serialized_data = MatrimonialProfileSerializer(saved_serializer).data
        return Response(
            {"message": "Matrimonial profile updated successfully", "data": serialized_data, "status": "success"},
            status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Create a user matrimonial profile for logged in user",
        description=
        """
        This endpoint allows an authenticated user to create a matrimonial profile for him/herself.
        """,
        request=CreateMatrimonialProfileSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Matrimonial Profile created successfully",
                response=MatrimonialProfileSerializer
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request. Maximum number of allowed images exceeded.",
            ),
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        images = self.request.FILES.getlist('images')
        if len(images) > 6:
            return Response({"message": "The maximum number of allowed images is 6", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        created_profile = serializer.save()
        serialized_data = MatrimonialProfileSerializer(created_profile).data

        return Response(
            {"message": "Matrimonial profile created successfully", "data": serialized_data, "status": "success"},
            status=status.HTTP_201_CREATED)


class RetrieveOtherUsersMatrimonialProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MatrimonialProfileSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Get another user matrimonial profile",
        description=
        """
        This endpoint allows an authenticated user to retrieve another user's matrimonial profile.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Matrimonial Profile retrieved successfully",
                response=MatrimonialProfileSerializer
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="User does not have matrimonial profile.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Matrimonial Profile ID is required."
            )
        }
    )
    def get(self, request, *args, **kwargs):
        matrimonial_profile_id = self.kwargs.get('matrimonial_profile_id')
        if matrimonial_profile_id is None:
            return Response({"message": "Matrimonial Profile ID is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                matrimonial_profile = MatrimonialProfile.objects.get(id=matrimonial_profile_id)
            except MatrimonialProfile.DoesNotExist:
                return Response({"message": "Matrimonial profile does not exist", "status": "failed"},
                                status=status.HTTP_404_NOT_FOUND)
            serialized_profile = MatrimonialProfileSerializer(matrimonial_profile).data
            return Response({"message": "Matrimonial profile retrieved successfully", "data": serialized_profile,
                             "status": "success"}, status=status.HTTP_200_OK)


class BookmarkUsersMatrimonialProfile(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MatrimonialProfileSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Add matrimonial profile to bookmarks list",
        description=
        """
        This endpoint allows an authenticated user to bookmark another user's matrimonial profile.
        """,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Matrimonial profile added to bookmark.",
                response=MatrimonialProfileSerializer,
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or missing matrimonial_profile_id.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Matrimonial profile not found.",
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        user = self.request.user
        matrimonial_profile_id = self.kwargs.get("matrimonial_profile_id")
        if not matrimonial_profile_id:
            return Response({"message": "Matrimonial profile id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            matrimonial_profile = MatrimonialProfile.objects.get(id=matrimonial_profile_id)
        except MatrimonialProfile.DoesNotExist:
            return Response({"message": "Invalid matrimonial profile id", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)

        if matrimonial_profile == self.request.user.matrimonial_profile:
            return Response({"message": "You can't bookmark your own matrimonial profile", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        matrimonial_profile, created = BookmarkedProfile.objects.get_or_create(user=user, profile=matrimonial_profile)

        if created:
            return Response({"message": "Matrimonial profile bookmarked", "status": "success"},
                            status=status.HTTP_201_CREATED)
        else:
            bookmarked_profile = [
                {
                    "id": matrimonial_profile.profile.id,
                    "full_name": matrimonial_profile.profile.full_name,
                    "short_bio:": matrimonial_profile.profile.short_bio,
                    "gender:": matrimonial_profile.profile.gender,
                    "religion": matrimonial_profile.profile.religion,
                    "country": matrimonial_profile.profile.country,
                    "city": matrimonial_profile.profile.city,
                    "education": matrimonial_profile.profile.education,
                    "profession": matrimonial_profile.profile.profession,
                    "income": matrimonial_profile.profile.income,
                    "age": matrimonial_profile.profile.age,
                    "height": matrimonial_profile.profile.height,
                    "images": [image.image for image in matrimonial_profile.profile.images.all()],
                }
            ]
            return Response({"message": "Matrimonial profile already bookmarked",
                             "data": bookmarked_profile, "status": "success"}, status=status.HTTP_200_OK)


class BookmarkMatrimonialProfileListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Retrieves all bookmarked matrimonial profile",
        description=
        """
        This endpoint allows an authenticated user to retrieve their bookmarked matrimonial profile.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="All bookmarked profiles fetched",
                response=MatrimonialProfileSerializer(many=True)
            ),
        }
    )
    def get(self, request):
        user = self.request.user
        bookmarked_profiles = BookmarkedProfile.objects.select_related('user', 'profile').filter(user=user)
        if not bookmarked_profiles.exists():
            return Response({"message": "Customer has no profile bookmarked", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serialized_data = [
            {
                "id": bp.profile.id,
                "full_name": bp.profile.full_name,
                "short_bio:": bp.profile.short_bio,
                "gender:": bp.profile.gender,
                "religion": bp.profile.religion,
                "country": bp.profile.country,
                "city": bp.profile.city,
                "education": bp.profile.education,
                "profession": bp.profile.profession,
                "income": bp.profile.income,
                "age": bp.profile.age,
                "height": bp.profile.height,
                "images": [image.image for image in bp.profile.images.all()],
            }.copy()
            for bp in bookmarked_profiles
        ]
        return Response({"message": "All bookmarked profiles fetched", "data": serialized_data, "status": "success"},
                        status=status.HTTP_200_OK)


class FilterMatrimonialProfilesView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MatrimonialProfileSerializer
    filterset_class = MatrimonialFilter
    filter_backends = [DjangoFilterBackend]
    queryset = MatrimonialProfile.objects.all()
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Filter Matrimonial Profile List",
        description=
        """
        This endpoint retrieves a list of filtered matrimonial profile.
        """,
        parameters=[
            OpenApiParameter(name="age", description="age (optional)", required=False),
            OpenApiParameter(name="religion", description="religion (optional)", required=False),
            OpenApiParameter(name="education", description="education (optional)", required=False),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Matrimonial profile filtered successfully.",
                response=MatrimonialProfileSerializer(many=True)
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Exclude the profile of the current user
        try:
            queryset = queryset.exclude(user=self.request.user)
        except MatrimonialProfile.DoesNotExist:
            return Response({"message": "You must have a matrimonial profile before filtering", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)

        serialized_data = [
            {
                "full_name": bp.full_name,
                "height": bp.height,
                "age": bp.age,
                "religion": bp.religion,
                "city": bp.city,
                "education": bp.education,
                "profession": bp.profession,
                "images": [image.image for image in bp.images.all()]
            }.copy()
            for bp in queryset
        ]
        return Response(
            {"message": "Matrimonial Profiles filtered successfully", "data": serialized_data, "status": "success"},
            status.HTTP_200_OK)


class ConnectionRequestListCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConnectionRequestSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Connection Request List",
        description=
        """
        This endpoint retrieves a list of connection requests.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="All connection requests fetched successfully",
                response=ConnectionRequestSerializer,
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
    )
    def get(self, request):
        user = self.request.user
        try:
            matrimonial_profile = MatrimonialProfile.objects.get(user=user)
        except MatrimonialProfile.DoesNotExist:
            return Response({"message": "User does not have a matrimonial profile", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        sent_requests = ConnectionRequest.objects.filter(sender=matrimonial_profile)
        received_requests = ConnectionRequest.objects.filter(receiver=matrimonial_profile)
        serialized_sent_requests = self.serializer_class(sent_requests, many=True, context={"request": request}).data
        serialized_received_requests = self.serializer_class(received_requests, many=True,
                                                             context={"request": request}).data
        return Response(
            {
                "message": "All connection requests fetched successfully",
                "sent_requests": serialized_sent_requests,
                "received_requests": serialized_received_requests,
                "status": "success"
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Create Connection Request",
        description=
        """
        This endpoint creates connection requests.
        """,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Connection request created successfully",
                response=ConnectionRequestSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Matrimonial profile does not exist."
            ),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Connection request created successfully", "status": "success"},
                        status=status.HTTP_201_CREATED)


class ConnectionRequestRetrieveUpdateView(GenericAPIView):
    serializer_class = ConnectionRequestSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Updates a Connection Request",
        description=
        """
        This endpoint allows only the receiver to update a connection requests.
        """,
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Connection request updated successfully",
                response=ConnectionRequestSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Connection request does not exist."
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Connection request id is required."
            ),
        },
    )
    def patch(self, request, *args, **kwargs):
        user = self.request.user
        connection_request_id = self.kwargs.get('connection_request_id')
        if connection_request_id is None:
            return Response({"message": "Connection request id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                connection_request = ConnectionRequest.objects.get(id=connection_request_id)
            except ConnectionRequest.DoesNotExist:
                return Response({"message": "Connection request does not exist", "status": "failed"},
                                status=status.HTTP_404_NOT_FOUND)
            receiver = connection_request.receiver.user
            if user != receiver:
                return Response(
                    {"message": "Only the receiver can change the status of the request", "status": "failed"},
                    status=status.HTTP_406_NOT_ACCEPTABLE)
            serializer = self.get_serializer(connection_request, data=request.data, partial=True,
                                             context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                {"message": "Connection request updated successfully", "data": serializer.data,
                 "status": "success"},
                status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Deletes a Connection Request",
        description=
        """
        This endpoint deletes a connection requests.
        """,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Connection request deleted successfully",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Connection request does not exist."
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Connection request id is required."
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        user = self.request.user
        connection_request_id = self.kwargs.get('connection_request_id')
        if connection_request_id is None:
            return Response({"message": "Connection request id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                connection_request = ConnectionRequest.objects.get(id=connection_request_id)
            except ConnectionRequest.DoesNotExist:
                return Response({"message": "Connection request does not exist", "status": "failed"},
                                status=status.HTTP_404_NOT_FOUND)
            receiver = connection_request.receiver.user
            if user != receiver:
                return Response(
                    {"message": "Only the receiver can delete the connection request", "status": "failed"},
                    status=status.HTTP_406_NOT_ACCEPTABLE)
            connection_request.delete()
            return Response({"message": "Connection request deleted successfully", "status": "failed"},
                            status=status.HTTP_204_NO_CONTENT)


class ConversationsListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationListSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Retrieve Conversation List",
        description=
        """
        This endpoint retrieve a conversation list.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Conversation list fetched successfully",
                response=ConversationListSerializer(many=True)
            ),
        },
    )
    def get(self, request):
        user = self.request.user
        try:
            matrimonial_profile = MatrimonialProfile.objects.get(user=user)
        except MatrimonialProfile.DoesNotExist:
            return Response({"message": "User does not have a matrimonial profile", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        conversation_list = Conversation.objects.filter(Q(initiator=matrimonial_profile) |
                                                        Q(receiver=matrimonial_profile))

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
            {"message": "Conversation list fetched successfully", "data": serializer.data, "status": "success"},
            status=status.HTTP_200_OK)


class RetrieveConversationView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Retrieve a conversation",
        description=
        """
        This endpoint retrieve a conversation.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Conversation fetched successfully",
                response=ConversationSerializer
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Conversation does not exist",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        convo_id = self.kwargs.get('convo_id')
        conversation = Conversation.objects.filter(id=convo_id)
        if not conversation.exists():
            return Response({"message": "Conversation does not exist", "status": "success"},
                            status=status.HTTP_404_NOT_FOUND)
        else:
            serializer = self.serializer_class(instance=conversation.get(), context={"request": request})
            return Response(
                {"message": "Conversation fetched successfully", "data": serializer.data, "status": "success"},
                status=status.HTTP_200_OK)


class CreateConversationView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationCreateSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Create a conversation",
        description=
        """
        This endpoint creates a conversation.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Conversation created successfully",
                response=ConversationSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Matrimonial profile does not exist",
            ),
        },
    )
    def post(self, request):
        with transaction.atomic():
            serializer = self.serializer_class(data=self.request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Create the chat
            conversation = serializer.save()

            data = {
                "id": conversation.id,
                "receiving_user": {
                    "id": conversation.receiver.id,
                    "full_name": conversation.receiver.full_name,
                },
                "receiver_profile_image": conversation.receiver.matrimonial_profile.images.first() or "",
                "message": conversation.messages.first().text,
                "attachment": conversation.messages.first().attachment or ""
            }
            return Response({"message": "Message sent successfully", "data": data, "status": "success"},
                            status=status.HTTP_201_CREATED)


class AddFavouriteProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Add profile to favorites",
        description=
        """
        This endpoint allows an authenticated user to add a matrimonial profile to their favorites list.
        """,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Profile added to favorites.",
                response=MatrimonialProfileSerializer
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or missing profile id.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Profile not found.",
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile_id = self.kwargs.get("profile_id")
        if not profile_id:
            return Response({"message": "Profile id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = MatrimonialProfile.objects.get(id=profile_id)
        except MatrimonialProfile.DoesNotExist:
            return Response({"message": "Invalid profile id", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)

        favourite, created = FavouriteProfile.objects.get_or_create(user=user, profile=profile)

        if created:
            return Response({"message": "Ad added to favourites", "status": "success"},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Ad already in favourites", "status": "success"}, status=status.HTTP_200_OK)


class ListFavouriteProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Retrieves all favorite matrimonial profiles",
        description=
        """
        This endpoint allows an authenticated user to retrieve their matrimonial profiles list.
        """,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="All favorite profiles fetched.",
                response=MatrimonialProfileSerializer(many=True)
            ),
        }
    )
    def get(self, request):
        user = self.request.user
        favourite_profiles = FavouriteProfile.objects.select_related('profile').filter(user=user)
        if not favourite_profiles.exists():
            return Response({"message": "User has no favourite profiles", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serialized_data = MatrimonialProfileSerializer(favourite_profiles, many=True).data
        return Response({"message": "All favorite products fetched", "data": serialized_data, "status": "success"},
                        status=status.HTTP_200_OK)
