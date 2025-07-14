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

    # Profile
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('api/profile/image/', ProfileImageView.as_view(), name='profile_image'),
    path('api/profile/<int:user_id>/', PublicProfileView.as_view(), name='public_profile'),
    
    # Legacy profile endpoint (keeping for compatibility)
    path('api/user/profile/', UserProfileView.as_view(), name='user_profile_legacy'),

    # API
    path('api/artworks/', ArtworkListCreateView.as_view(), name='artwork_list_create'),
    path('api/orders/', OrderCreateView.as_view(), name='order_create'),
    path('api/follow/', FollowView.as_view(), name='follow'),
    path('api/like/', LikeView.as_view(), name='like'),
    path('api/artwork/<int:artwork_id>/comments/', CommentListCreateView.as_view(), name='comments'),
    path('api/artist/dashboard/', ArtistDashboardView.as_view(), name='artist_dashboard'),
    path('api/wishlist/', WishlistView.as_view(), name='wishlist'),

]
