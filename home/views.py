from django.shortcuts import render

# Create your views here.
# views.py
from rest_framework import generics, permissions
from .models import *
from .serializers import RegisterSerializer, ArtworkSerializer, OrderSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from home.serializers import UserSerializer  # We'll define this next
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers


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
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
            attrs["username"] = user.username
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        return super().validate(attrs)

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
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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


# views.py

from rest_framework import generics, permissions
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
