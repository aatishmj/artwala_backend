# your_app_name/urls.py
from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView



urlpatterns = [
    # Auth
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('api/logout/', logout_view, name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('api/auth/validate-reset/', ValidateResetTokenView.as_view(), name='validate_reset'),
    path('api/auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),

    # Profile
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('api/profile/image/', ProfileImageView.as_view(), name='profile_image'),
    path('api/profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('api/profile/<int:user_id>/', PublicProfileView.as_view(), name='public_profile'),
    
    # User Statistics
    path('api/user/stats/', UserStatsView.as_view(), name='user_stats'),
    path('api/user/<int:user_id>/stats/', UserStatsView.as_view(), name='user_stats_by_id'),
    
    # Profile Completion Details
    path('api/profile/completion/', ProfileCompletionView.as_view(), name='profile_completion'),
    
    # Artist Recommendations
    path('api/artists/recommendations/', ArtistRecommendationsView.as_view(), name='artist_recommendations'),
    
    # Legacy profile endpoint (keeping for compatibility)
    path('api/user/profile/', UserProfileView.as_view(), name='user_profile_legacy'),

    # API
    path('api/artworks/', ArtworkListCreateView.as_view(), name='artwork_list_create'),
    path('api/artworks/<int:pk>/', ArtworkDetailView.as_view(), name='artwork_detail'),
    path('api/orders/', OrderCreateView.as_view(), name='order_create'),
    path('api/orders/<int:pk>/', OrderUpdateView.as_view(), name='order_update'),
    path('api/user/orders/', UserOrdersListView.as_view(), name='user_orders'),
    path('api/artist/orders/', ArtistOrdersListView.as_view(), name='artist_orders'),
    path('api/follow/', FollowView.as_view(), name='follow'),
    path('api/like/', LikeView.as_view(), name='like'),
    path('api/artwork/<int:artwork_id>/comments/', CommentListCreateView.as_view(), name='comments'),
    path('api/artist/dashboard/', ArtistDashboardView.as_view(), name='artist_dashboard'),
    path('api/wishlist/', WishlistView.as_view(), name='wishlist'),
    path('api/artist/artworks/', ArtistArtworksListView.as_view(), name='artist-artworks'),
    path('api/messages/<int:recipient_id>/', MessageListView.as_view(), name='messages'),
    path('api/messages/', ConversationsListView.as_view(), name='conversations'),
    path('api/messages/detail/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('api/following/', FollowingView.as_view(), name='following'),
    path('api/categories/', CategoriesView.as_view(), name='categories'),
]
