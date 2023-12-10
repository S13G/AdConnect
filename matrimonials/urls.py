from django.urls import path

from ads import consumers
from matrimonials import views

urlpatterns = [
    path('bookmark/<str:matrimonial_profile_id>/', views.BookmarkUsersMatrimonialProfile.as_view(),
         name="bookmark_matrimonial_profile"),
    path('bookmark/matrimonial_profile/all/', views.BookmarkMatrimonialProfileListView.as_view(),
         name="all_bookmarked_matrimonial_profile"),
    path('connection-requests/', views.ConnectionRequestListCreateView.as_view(), name='connection-request-list'),
    path('connection-requests/<str:connection_request_id>/', views.ConnectionRequestRetrieveUpdateView.as_view(),
         name='connection-request-detail'),
    path('conversations/all/', views.ConversationsListView.as_view(), name="conversations_list"),
    path('conversation/<str:convo_id>/', views.RetrieveConversationView.as_view(), name='get_conversation'),
    path('profile/conversation/start/', views.CreateConversationView.as_view(), name='start_conversation'),
    path('favourite-profiles/<str:profile_id>/add/', views.AddFavouriteProfileView.as_view(),
         name="add_favourite_profile"),
    path('favourite-profiles/', views.ListFavouriteProfileView.as_view(), name="favourite_profiles_list"),
    path('matrimonial-profile/all/', views.RetrieveAllMatrimonialProfilesView.as_view(),
         name="retrieve_all_matrimonial_profile"),
    path('matrimonial-profile/', views.RetrieveCreateUpdateMatrimonialProfileView.as_view(),
         name="retrieve_create_matrimonial_profile"),
    path('matrimonial-profile/<str:matrimonial_profile_id>/',
         views.RetrieveOtherUsersMatrimonialProfileView.as_view(),
         name="retrieve_user_matrimonial_profile"),
    path('matrimonial_profile/filters/', views.FilterMatrimonialProfilesView.as_view(),
         name="matrimonial_profile_filters"),
]


websocket_urlpatterns = [
    path("ws/conversation/<str:id>/", consumers.ChatConsumer.as_asgi()),
]
