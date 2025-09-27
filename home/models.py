from django.db import models

# Create your models here.
# models.py

from django.utils.timezone import now
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model for both regular users and artists.
    New artist fields are temporarily added here for the launch.
    TODO: Refactor these new fields into a separate ArtistProfile model post-launch.
    """
    USER_TYPE_CHOICES = (
        ('artist', 'Artist'),
        ('user', 'User'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    
    # --- Existing Profile fields (common to all users) ---
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    
    # --- Existing Social media handles ---
    instagram_handle = models.CharField(max_length=50, blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    
    # --- Existing Artist-specific fields (Kept for compatibility) ---
    is_verified = models.BooleanField(default=False)
    artist_since = models.DateTimeField(blank=True, null=True)

    # --- NEW ARTIST FIELDS (Added for launch) ---
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    
    # Address Details
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True) # Added for completeness
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    
    # Documents
    aadhaar_card = models.ImageField(upload_to='documents/aadhaar/', blank=True, null=True)
    pan_card = models.ImageField(upload_to='documents/pan/', blank=True, null=True)

    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True)
    account_holder_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    
    # --- MEMBERSHIP FIELDS (Added for membership functionality) ---
    is_member = models.BooleanField(default=False)
    membership_purchase_date = models.DateTimeField(null=True, blank=True)
    membership_expiry_date = models.DateTimeField(null=True, blank=True)
    membership_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_stats(self):
        """Calculate comprehensive user/artist stats"""
        from django.db.models import Sum, Count
        
        if self.user_type == 'artist':
            # Calculate total views for artist's artworks (once view_count is added)
            total_views = 0  # Will be: self.artworks.aggregate(Sum('view_count'))['view_count__sum'] or 0
            
            # Calculate total likes received on artist's artworks
            total_likes_received = Like.objects.filter(artwork__artist=self).count()
            
            # Calculate completed orders for revenue
            completed_orders = Order.objects.filter(
                artwork__artist=self, 
                status='delivered'
            )
            
            # Calculate total revenue from completed transactions
            total_revenue = completed_orders.aggregate(
                total=Sum('artwork__price')
            )['total'] or 0
            
            return {
                'artworks_count': self.artworks.count(),
                'followers_count': self.followers.count(),
                'following_count': self.following.count(),
                'total_likes_received': total_likes_received,
                'total_views': total_views,
                'total_sales': completed_orders.count(),
                'total_revenue': float(total_revenue),
                'profile_completion': self.calculate_profile_completion(),
                'is_member': self.is_member,
                'membership_expiry_date': self.membership_expiry_date,
            }
        else:
            return {
                'following_count': self.following.count(),
                'followers_count': self.followers.count(),
                'likes_given': self.like_set.count(),
                'saved_artworks': self.wishlist.count(),
                'orders_count': self.orders.count(),
                'is_member': self.is_member,
                'profile_completion': self.calculate_profile_completion(),
            }

    def calculate_profile_completion(self):
        """Calculate profile completion percentage with detailed breakdown"""
        completion_data = {
            'percentage': 0,
            'completed_fields': [],
            'missing_fields': [],
            'total_fields': 0,
            'completed_count': 0
        }
        
        # Basic fields (for all users)
        basic_field_checks = [
            ('first_name', 'First Name', self.first_name),
            ('last_name', 'Last Name', self.last_name),
            ('bio', 'Bio', self.bio),
            ('location', 'Location', self.location),
            ('profile_image', 'Profile Image', self.profile_image),
        ]
        
        for field_name, field_label, field_value in basic_field_checks:
            completion_data['total_fields'] += 1
            if field_value:
                completion_data['completed_count'] += 1
                completion_data['completed_fields'].append({
                    'field': field_name,
                    'label': field_label
                })
            else:
                completion_data['missing_fields'].append({
                    'field': field_name,
                    'label': field_label
                })
        
        # Artist-specific fields
        if self.user_type == 'artist':
            artist_field_checks = [
                ('website', 'Website', self.website),
                ('instagram_handle', 'Instagram Handle', self.instagram_handle),
                ('twitter_handle', 'Twitter Handle', self.twitter_handle),
                ('artist_since', 'Artist Since', self.artist_since),
            ]
            
            for field_name, field_label, field_value in artist_field_checks:
                completion_data['total_fields'] += 1
                if field_value:
                    completion_data['completed_count'] += 1
                    completion_data['completed_fields'].append({
                        'field': field_name,
                        'label': field_label
                    })
                else:
                    completion_data['missing_fields'].append({
                        'field': field_name,
                        'label': field_label
                    })
        
        # Calculate percentage
        if completion_data['total_fields'] == 0:
            completion_data['percentage'] = 0
        else:
            completion_data['percentage'] = round(
                (completion_data['completed_count'] / completion_data['total_fields']) * 100
            )
        
        return completion_data

    def activate_membership(self, amount, payment_method, payment_id):
        """Activate membership for the user"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.is_member = True
        self.membership_purchase_date = timezone.now()
        self.membership_expiry_date = timezone.now() + timedelta(days=365)  # 1 year
        self.membership_amount = amount
        self.payment_method = payment_method
        self.payment_id = payment_id
        self.save()
        
        return self


# models.py
class Artwork(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    medium = models.CharField(max_length=100, blank=True)
    dimensions = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_available = models.BooleanField(default=True)
    stock = models.IntegerField(default=1)
    view_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    image = models.ImageField(upload_to='artworks/images/')
    video = models.FileField(upload_to='artworks/videos/', blank=True, null=True)

    artist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artworks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.artist.username}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"

class Transaction(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50, default='pending')
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction for Order #{self.order.id}"

from django.db import models
from django.utils import timezone
from datetime import timedelta

class Membership(models.Model):
    """Record of a membership purchase for an artist/user."""
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='memberships')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=50, default='pending')
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # New field for expiry
    expiry_date = models.DateTimeField(blank=True, null=True)  # auto-set on creation

    def save(self, *args, **kwargs):
        # If new membership and expiry_date not set, set it for 1 year
        if not self.expiry_date:
            # timestamp is only set after the first save (auto_now_add), so fall back to now()
            base = self.timestamp if self.timestamp else timezone.now()
            self.expiry_date = base + timedelta(days=365)  # yearly plan
        super().save(*args, **kwargs)

        # Update user's is_member flag immediately if payment successful
        if self.payment_status == 'completed':
            self.user.is_member = True
            self.user.save(update_fields=['is_member'])

    def is_active(self):
        """Check if membership is still active"""
        return self.expiry_date and self.expiry_date > timezone.now()

    def __str__(self):
        return f"Membership #{self.id} for {self.user.username} - {self.payment_status}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'artwork')  # Prevent duplicates

    def __str__(self):
        return f"{self.user.username} likes {self.artwork.title}"

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')  # prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='likes')
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'artwork')  # only 1 like per user per artwork

    def __str__(self):
        return f"{self.user.username} liked {self.artwork.title}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.artwork.title}"
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True)  # SHA256 hash
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'expires_at']),
        ]

    def __str__(self):
        return f"Reset token for {self.user.username}"

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
