from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User, Artwork, Order, Transaction, Follow, Like, Comment, Wishlist

admin.site.register(User)
admin.site.register(Artwork)
admin.site.register(Order)
admin.site.register(Transaction)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Wishlist)
