from django.shortcuts import render

# Create your views here.
# views.py
from rest_framework import generics, permissions
from .models import *

from .serializers import *

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import models


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
# views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Support both email and username login
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        if not username_or_email:
            raise serializers.ValidationError("Username or email is required")

        try:
            # Try to find user by email first, then by username
            if '@' in username_or_email:
                user = User.objects.get(email=username_or_email)
            else:
                user = User.objects.get(username=username_or_email)
            
            # Set the username for JWT validation
            attrs["username"] = user.username
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        # Get the token data
        data = super().validate(attrs)
        
        # Add user data to response
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        data['message'] = 'Login successful'
        
        return data

# replace view
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class ArtistDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type != 'artist':
            return Response({'detail': 'Access denied: Only artists allowed.'}, status=403)

        artworks = Artwork.objects.filter(artist=user)
        total_artworks = artworks.count()

        orders = Order.objects.filter(artwork__artist=user)
        total_orders = orders.count()

        total_revenue = sum(order.artwork.price for order in orders)

        return Response({
            'total_artworks': total_artworks,
            'total_orders': total_orders,
            'total_revenue': total_revenue
        })
    

from rest_framework.response import Response
from rest_framework import status

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        print("Incoming data:", request.data)  # 🔍 Log data
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens for the new user
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Return user data with tokens
            user_serializer = UserSerializer(user)
            return Response({
                'user': user_serializer.data,
                'access': str(access),
                'refresh': str(refresh),
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        print("Serializer errors:", serializer.errors)  # 🔍 Log errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArtworkListCreateView(generics.ListCreateAPIView):
    queryset = Artwork.objects.all()
    serializer_class = ArtworkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]


# Profile Views
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's profile"""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update current user's profile"""
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return updated profile
            profile_serializer = ProfileSerializer(request.user)
            return Response(profile_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Upload profile image"""
        serializer = ProfileImageSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            profile_serializer = ProfileSerializer(request.user)
            return Response(profile_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PublicProfileView(APIView):
    """View public profile of any user/artist"""
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = ProfileSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

# New User Statistics API endpoint
class UserStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id=None):
        """
        Get comprehensive user statistics
        If user_id is not provided, returns stats for the authenticated user
        """
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user
            
        serializer = UserStatsSerializer(user)
        return Response(serializer.data)

# Enhanced Profile Update with statistics
class ProfileUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Add updated profile completion percentage
        user = self.get_object()
        response.data['profile_completion'] = user.calculate_profile_completion()
        return response

# Artist Recommendations API
class ArtistRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get recommended artists for dashboard"""
        # Get trending artists (those with most followers/recent activity)
        trending_artists = User.objects.filter(
            user_type='artist',
            is_verified=True
        ).exclude(
            id=request.user.id  # Exclude current user
        ).annotate(
            follower_count=models.Count('followers')
        ).order_by('-follower_count', '-date_joined')[:6]
        
        # Get new artists (recently joined)
        new_artists = User.objects.filter(
            user_type='artist'
        ).exclude(
            id=request.user.id
        ).order_by('-date_joined')[:4]
        
        # Serialize the data
        trending_serializer = ProfileSerializer(trending_artists, many=True)
        new_serializer = ProfileSerializer(new_artists, many=True)
        
        return Response({
            'trending_artists': trending_serializer.data,
            'new_artists': new_serializer.data,
            'recommended_count': len(trending_artists) + len(new_artists)
        })

# Profile Completion Details API
class ProfileCompletionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get detailed profile completion information"""
        completion_data = request.user.calculate_profile_completion()
        return Response(completion_data)

# views.py

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from .models import Follow, Like, Comment
from .serializers import FollowSerializer, LikeSerializer, CommentSerializer

class FollowView(generics.CreateAPIView):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)

class LikeView(generics.CreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        artwork_id = self.kwargs['artwork_id']
        return Comment.objects.filter(artwork_id=artwork_id)

    def perform_create(self, serializer):
        artwork_id = self.kwargs['artwork_id']
        serializer.save(user=self.request.user, artwork_id=artwork_id)

# Logout endpoint
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=200)
    except Exception as e:
        return Response({"error": "Invalid token"}, status=400)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist = Wishlist.objects.filter(user=request.user).select_related('artwork')
        serializer = WishlistSerializer(wishlist, many=True)
        return Response(serializer.data)

    def post(self, request):
        artwork_id = request.data.get('artwork_id')
        if not artwork_id:
            return Response({"error": "artwork_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            artwork = Artwork.objects.get(id=artwork_id)
        except Artwork.DoesNotExist:
            return Response({"error": "Artwork not found"}, status=status.HTTP_404_NOT_FOUND)

        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, artwork=artwork)
        if not created:
            return Response({"message": "Already in wishlist"}, status=status.HTTP_200_OK)

        serializer = WishlistSerializer(wishlist_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class WishlistItemDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, artwork_id):
        try:
            artwork = Artwork.objects.get(id=artwork_id)
        except Artwork.DoesNotExist:
            return Response({"error": "Artwork not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            wishlist_item = Wishlist.objects.get(user=request.user, artwork=artwork)
            wishlist_item.delete()
            return Response({"message": "Removed from wishlist"}, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response({"error": "Item not found in wishlist"}, status=status.HTTP_404_NOT_FOUND)