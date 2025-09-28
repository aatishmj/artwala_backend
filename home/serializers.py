# serializers.py
import json
from decimal import Decimal
from rest_framework import serializers
from .models import User, Artwork, Order, Message
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from home.models import User

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    membership_expiry_date = serializers.DateTimeField(read_only=True)
    membership_purchase_date = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone', 'profile_image', 'bio', 'location', 'website',
            'instagram_handle', 'twitter_handle', 'is_verified', 'artist_since',
            'date_joined', 'is_member', 'membership_purchase_date', 'membership_expiry_date',
            'membership_amount', 'payment_method', 'payment_id'
        ]
        read_only_fields = [
            'id', 'username', 'email', 'user_type', 'date_joined', 'is_verified',
            'artist_since', 'is_member', 'membership_purchase_date', 'membership_expiry_date',
            'membership_amount', 'payment_method', 'payment_id'
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
    artist = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    description = serializers.CharField(allow_blank=True, required=False)
    price = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

    class Meta:
        model = Artwork
        fields = ['id','title','description','price','stock','image','video','artist','created_at','category','medium','dimensions','tags','is_available','view_count','likes_count','is_featured']
        read_only_fields = ['id','artist','created_at','likes_count','view_count','is_featured']

    def to_internal_value(self, data):
        data = data.copy()
        if 'price' in data and data['price'] == '':
            data['price'] = None
        if 'tags' in data and isinstance(data['tags'], str):
            try:
                data['tags'] = json.loads(data['tags'])
            except json.JSONDecodeError:
                data['tags'] = []
        return super().to_internal_value(data)

    def get_likes_count(self, obj):
        return obj.likes.count()

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
    artwork = ArtworkSerializer(read_only=True)
    artwork_id = serializers.PrimaryKeyRelatedField(
        queryset=Artwork.objects.all(),
        source='artwork',
        write_only=True
    )
    buyer = UserSerializer(read_only=True)
    transaction = serializers.SerializerMethodField()
    commission = serializers.SerializerMethodField()
    net_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'artwork', 'artwork_id', 'buyer', 'quantity', 'status', 'created_at', 'transaction', 'commission', 'net_amount']

    def get_transaction(self, obj):
        try:
            transaction = obj.transaction
            return {
                'amount': transaction.amount,
                'payment_status': transaction.payment_status,
                'payment_method': transaction.payment_method,
                'timestamp': transaction.timestamp
            }
        except:
            return None

    def get_commission(self, obj):
        amount = obj.artwork.price * obj.quantity
        return amount * Decimal('0.1')  # 10% commission

    def get_net_amount(self, obj):
        amount = obj.artwork.price * obj.quantity
        return amount - (amount * Decimal('0.1'))
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
    membership_expiry_date = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone', 'profile_image', 'bio', 'location', 'website',
            'instagram_handle', 'twitter_handle', 'is_verified', 'artist_since',
            'date_joined', 'stats', 'is_member', 'membership_purchase_date', 
            'membership_expiry_date', 'membership_amount'
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

    def validate_profile_image(self, value):
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file too large ( > 5MB )")
            # Check file type
            if not value.content_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                raise serializers.ValidationError("Unsupported file type. Use JPEG, PNG, GIF, or WebP.")
        return value



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
    membership_expiry_date = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'user_type', 'bio', 'location',
            'profile_image', 'date_joined', 'last_login', 'stats', 'profile_completion',
            'is_member', 'membership_purchase_date', 'membership_expiry_date'
        ]
        read_only_fields = fields  # All fields are read-only for stats endpoint
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "recipient", "content", "timestamp", "is_read"]
        read_only_fields = ["id", "timestamp"]

# Password Reset Serializers
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("No active account found with this email address.")
        return value

class ValidateResetSerializer(serializers.Serializer):
    token = serializers.CharField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
# serializers.py - Add this serializer
class MembershipPurchaseSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, write_only=True)
    payment_method = serializers.CharField(write_only=True)
    payment_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'phone', 'address_line_1', 'address_line_2', 'city', 'state', 'pincode',
            'aadhaar_card', 'pan_card', 'bank_name', 'account_number', 'ifsc_code', 
            'bank_branch', 'account_holder_name', 'birth_date', 'gender',
            'amount', 'payment_method', 'payment_id'
        ]
    
    def validate(self, data):
        # Required fields validation
        required_fields = [
            'phone', 'address_line_1', 'city', 'state', 'pincode',
            'bank_name', 'account_number', 'ifsc_code', 'account_holder_name',
            'birth_date', 'gender'
        ]
        
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required")
        
        return data
    
    def update(self, instance, validated_data):
        # Extract payment data
        amount = validated_data.pop('amount', 0)
        payment_method = validated_data.pop('payment_method', '')
        payment_id = validated_data.pop('payment_id', '')
        
        # Update user fields with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle file uploads separately
        if 'aadhaar_card' in self.context['request'].FILES:
            instance.aadhaar_card = self.context['request'].FILES['aadhaar_card']
        if 'pan_card' in self.context['request'].FILES:
            instance.pan_card = self.context['request'].FILES['pan_card']
        
        # Activate membership
        instance.activate_membership(amount, payment_method, payment_id)
        
        return instance

class MembershipSerializer(serializers.ModelSerializer):
    """Serializer specifically for membership details"""
    class Meta:
        model = User
        fields = [
            'is_member', 'membership_purchase_date', 'membership_expiry_date',
            'membership_amount', 'payment_method'
        ]
        read_only_fields = fields
