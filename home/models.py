from django.db import models

# Create your models here.
# models.py


from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('artist', 'Artist'),
        ('user', 'User'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    
    # Profile fields
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    
    # Social media handles
    instagram_handle = models.CharField(max_length=50, blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    
    # Artist-specific fields
    is_verified = models.BooleanField(default=False)
    artist_since = models.DateTimeField(blank=True, null=True)

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
            total_revenue = Transaction.objects.filter(
                order__in=completed_orders
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            return {
                'artworks_count': self.artworks.count(),
                'followers_count': self.followers.count(),
                'following_count': self.following.count(),
                'total_likes_received': total_likes_received,
                'total_views': total_views,
                'total_sales': completed_orders.count(),
                'total_revenue': float(total_revenue),
                'profile_completion': self.calculate_profile_completion(),
            }
        else:
            return {
                'following_count': self.following.count(),
                'followers_count': self.followers.count(),
                'likes_given': self.like_set.count(),
                'saved_artworks': self.wishlist.count(),
                'orders_count': self.orders.count(),
                'profile_completion': self.calculate_profile_completion(),
            }

    def calculate_profile_completion(self):
        """Calculate profile completion percentage"""
        total_fields = 0
        completed_fields = 0
        
        # Basic fields (for all users)
        basic_fields = [
            self.first_name,
            self.last_name,
            self.bio,
            self.location,
            self.profile_image,
        ]
        
        for field in basic_fields:
            total_fields += 1
            if field:
                completed_fields += 1
        
        # Artist-specific fields
        if self.user_type == 'artist':
            artist_fields = [
                self.website,
                self.instagram_handle,
                self.twitter_handle,
                self.artist_since,
            ]
            
            for field in artist_fields:
                total_fields += 1
                if field:
                    completed_fields += 1
        
        # Calculate percentage
        if total_fields == 0:
            return 0
        
        return round((completed_fields / total_fields) * 100)



# models.py
class Artwork(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)  # ➤ Stock available

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
