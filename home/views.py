from django.shortcuts import render

# Create your views here.
# views.py
from rest_framework import generics, permissions, status
from .models import *

from .serializers import *

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import models
from django.db.models import Count

# Password reset imports
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
import hashlib
from django.utils import timezone
from rest_framework.throttling import AnonRateThrottle


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
    queryset = Artwork.objects.all().order_by('-created_at')
    serializer_class = ArtworkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        artist_id = self.request.query_params.get('artist')
        if artist_id and artist_id.isdigit():
            qs = qs.filter(artist_id=artist_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise serializers.ValidationError('Authentication required')
        if getattr(user, 'user_type', None) != 'artist':
            raise serializers.ValidationError('Only artist accounts can upload artworks')
        serializer.save(artist=user)

class ArtworkDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Artwork.objects.all()
    serializer_class = ArtworkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def check_object_permissions(self, request, obj):
        # Only the artist owner may modify
        if request.method in ('PUT','PATCH','DELETE'):
            if not request.user.is_authenticated or obj.artist_id != request.user.id:
                raise serializers.ValidationError('Not permitted to modify this artwork')
        return super().check_object_permissions(request, obj)

class UserOrdersListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related('artwork', 'artwork__artist', 'transaction').order_by('-created_at')

class ArtistOrdersListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type != 'artist':
            return Order.objects.none()
        return Order.objects.filter(artwork__artist=self.request.user).select_related('artwork', 'buyer', 'transaction').order_by('-created_at')

class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(buyer=self.request.user)
        # For MVP, allow buying even if stock insufficient, reduce stock
        order.artwork.stock -= order.quantity
        order.artwork.save()
        # Create transaction (assuming payment is handled elsewhere, but for now, create with pending)
        Transaction.objects.create(
            order=order,
            amount=order.artwork.price * order.quantity,
            payment_method='card',  # Placeholder
            payment_status='completed'  # Assume success for MVP
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class OrderUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Artists can update their orders, users their own
        user = self.request.user
        if user.user_type == 'artist':
            return Order.objects.filter(artwork__artist=user)
        return Order.objects.filter(buyer=user)

class UserOrdersListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related('artwork', 'artwork__artist', 'transaction').order_by('-created_at')

class ArtistOrdersListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type != 'artist':
            return Order.objects.none()
        return Order.objects.filter(artwork__artist=self.request.user).select_related('artwork', 'buyer', 'transaction').order_by('-created_at')


class ArtistArtworksListView(generics.ListAPIView):
    serializer_class = ArtworkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Artwork.objects.filter(artist=self.request.user).select_related('artist').annotate(likes_count=Count('likes')).order_by('-created_at')

        # Ensure the authenticated user is set as the buyer
        serializer.save(buyer=self.request.user)


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
        try:
            serializer = ProfileImageSerializer(request.user, data=request.data, files=request.FILES, partial=True)
            if serializer.is_valid():
                serializer.save()
                profile_serializer = ProfileSerializer(request.user)
                return Response(profile_serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Profile image upload error for user {request.user.id}: {str(e)}")
            return Response({"detail": "Failed to upload image. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    def delete(self, request):
        artwork_id = request.data.get('artwork_id')
        if not artwork_id:
            return Response({"error": "artwork_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            artwork = Artwork.objects.get(id=artwork_id)
        except Artwork.DoesNotExist:
            return Response({"error": "Artwork not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            wishlist_item = Wishlist.objects.get(user=request.user, artwork=artwork)
            wishlist_item.delete()
            return Response({"message": "Removed from wishlist"}, status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response({"error": "Item not found in wishlist"}, status=status.HTTP_404_NOT_FOUND)


class MessageListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        recipient_id = self.kwargs.get("recipient_id")
        if recipient_id:
            # Get conversation between current user and recipient
            return Message.objects.filter(
                (models.Q(sender=self.request.user) & models.Q(recipient_id=recipient_id)) |
                (models.Q(sender_id=recipient_id) & models.Q(recipient=self.request.user))
            ).order_by("timestamp")
        return Message.objects.none()

    def perform_create(self, serializer):
        recipient_id = self.kwargs.get("recipient_id")
        serializer.save(sender=self.request.user, recipient_id=recipient_id)

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            models.Q(sender=self.request.user) | models.Q(recipient=self.request.user)
        )


class ConversationsListView(generics.ListAPIView):
    serializer_class = UserSerializer  # Or create a custom serializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get distinct users that the current user has conversations with
        sent_to = Message.objects.filter(sender=self.request.user).values_list('recipient', flat=True).distinct()
        received_from = Message.objects.filter(recipient=self.request.user).values_list('sender', flat=True).distinct()
        user_ids = set(sent_to) | set(received_from)
        return User.objects.filter(id__in=user_ids).exclude(id=self.request.user.id)

class FollowingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        following = Follow.objects.filter(follower=request.user).select_related('following')
        serializer = ProfileSerializer([f.following for f in following], many=True)
        return Response(serializer.data)

class CategoriesView(APIView):
    def get(self, request):
        categories = Artwork.objects.values_list('category', flat=True).distinct()
        return Response(list(categories))

# Password Reset Views
class ForgotPasswordView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.validated_data['email'])
            # Generate token
            token = get_random_string(64)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            expires_at = timezone.now() + timezone.timedelta(hours=1)
            ip_address = self.get_client_ip(request)
            PasswordResetToken.objects.create(
                user=user,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address
            )
            # Send email
            reset_url = f"http://localhost:3000/auth/reset-password?token={token}"  # Adjust for prod
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_url}',
                'noreply@artwala.com',
                [user.email],
                fail_silently=False,
            )
            return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ValidateResetTokenView(APIView):
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'valid': False, 'message': 'Token required.'}, status=status.HTTP_400_BAD_REQUEST)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            reset_token = PasswordResetToken.objects.get(token_hash=token_hash)
            if reset_token.used or reset_token.is_expired():
                return Response({'valid': False, 'expired': True, 'message': 'Token is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'valid': True, 'message': 'Token is valid.'}, status=status.HTTP_200_OK)
        except PasswordResetToken.DoesNotExist:
            return Response({'valid': False, 'message': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            try:
                reset_token = PasswordResetToken.objects.get(token_hash=token_hash)
                if reset_token.used or reset_token.is_expired():
                    return Response({'message': 'Token is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
                # Reset password
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                # Mark token as used
                reset_token.used = True
                reset_token.save()
                # Generate new JWT tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Password reset successful.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }, status=status.HTTP_200_OK)
            except PasswordResetToken.DoesNotExist:
                return Response({'message': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# views.py - Add this view
class MembershipPurchaseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Check if user is already a member
        if request.user.is_member:
            return Response(
                {'detail': 'You are already a member'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MembershipPurchaseSerializer(
            request.user, 
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'message': 'Membership purchased successfully!',
                'user': UserSerializer(user).data,
                'membership_details': {
                    'is_member': user.is_member,
                    'purchase_date': user.membership_purchase_date,
                    'expiry_date': user.membership_expiry_date,
                    'amount': user.membership_amount
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
