# serializers.py
from rest_framework import serializers
from .models import User, Artwork, Order
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from home.models import User

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone', 'profile_image', 'bio', 'location', 'website',
            'instagram_handle', 'twitter_handle', 'is_verified', 'artist_since',
            'date_joined'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type', 'phone'
        )

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        user.is_active = True
        user.save()
        return user


class ArtworkSerializer(serializers.ModelSerializer):
    artist = serializers.ReadOnlyField(source='artist.id')
    description = serializers.CharField(allow_blank=True, required=False)
    price = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

    class Meta:
        model = Artwork
        fields = ['id','title','description','price','stock','image','video','artist','created_at']
        read_only_fields = ['id','artist','created_at']

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Price must be non-negative')
        return value

    def create(self, validated_data):
        if 'price' not in validated_data:
            validated_data['price'] = 0
        if 'description' not in validated_data:
            validated_data['description'] = ''
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'price' in validated_data and validated_data['price'] is None:
            validated_data['price'] = 0
        if 'description' in validated_data and validated_data['description'] is None:
            validated_data['description'] = ''
        return super().update(instance, validated_data)

class OrderSerializer(serializers.ModelSerializer):
    artwork = serializers.PrimaryKeyRelatedField(queryset=Artwork.objects.all())
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)

    class Meta:
        model = Order
        fields = ['id', 'artwork', 'buyer', 'quantity', 'status', 'created_at']
        read_only_fields = ['id', 'buyer', 'status', 'created_at']
# serializers.py

from rest_framework import serializers
from .models import Follow, Like, Comment

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'followed_at']
        read_only_fields = ['id', 'followed_at']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'artwork', 'liked_at']
        read_only_fields = ['id', 'liked_at']

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'artwork', 'content', 'created_at', 'username']
        read_only_fields = ['id', 'created_at', 'username']

class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    stats = serializers.ReadOnlyField(source='get_stats')
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone', 'profile_image', 'bio', 'location', 'website',
            'instagram_handle', 'twitter_handle', 'is_verified', 'artist_since',
            'date_joined', 'stats'
        ]
        read_only_fields = ['id', 'username', 'email', 'user_type', 'date_joined', 'is_verified']

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'bio', 'location', 'website',
            'instagram_handle', 'twitter_handle'
        ]

class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['profile_image']



#---------------------Wishlist---------------------------------

from rest_framework import serializers
from .models import Wishlist

class WishlistSerializer(serializers.ModelSerializer):
    artwork = ArtworkSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'artwork', 'added_on']

class UserStatsSerializer(serializers.ModelSerializer):
    """Serializer specifically for user statistics endpoint"""
    full_name = serializers.ReadOnlyField()
    stats = serializers.ReadOnlyField(source='get_stats')
    profile_completion = serializers.ReadOnlyField(source='calculate_profile_completion')
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'user_type', 'bio', 'location',
            'profile_image', 'date_joined', 'last_login', 'stats', 'profile_completion'
        ]
        read_only_fields = fields  # All fields are read-only for stats endpoint

