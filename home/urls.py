# your_app_name/urls.py
from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



urlpatterns = [
    # Auth
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # APIapi/
    path('api/artworks/', ArtworkListCreateView.as_view(), name='artwork_list_create'),
    path('api/orders/', OrderCreateView.as_view(), name='order_create'),
    path('api/follow/', FollowView.as_view(), name='follow'),
    path('api/like/', LikeView.as_view(), name='like'),
    path('api/artwork/<int:artwork_id>/comments/', CommentListCreateView.as_view(), name='comments'),
    path('api/profile/', UserProfileView.as_view(), name='user_profile'),
    path('api/artist/dashboard/', ArtistDashboardView.as_view(), name='artist_dashboard'),


]
