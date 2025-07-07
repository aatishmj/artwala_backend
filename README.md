# Artwala Backend API

Django REST API backend for the Artwala art marketplace platform.

## Features

### ✅ Phase 1 - Authentication System
- User registration and login
- JWT token-based authentication with refresh tokens
- Token blacklisting for secure logout
- Role-based access control (Artist vs User)
- Custom user model with user_type field

### ✅ Phase 2 - Profile Management
- Extended user profiles with bio, location, website
- Profile image upload and management
- Social media links (Instagram, Twitter)
- Artist verification system
- User statistics (followers, artworks, sales, etc.)

## API Endpoints

### Authentication
- `POST /auth/api/register/` - User registration
- `POST /auth/api/login/` - User login (accepts username or email)
- `POST /auth/api/logout/` - User logout with token blacklisting
- `POST /auth/api/token/refresh/` - Refresh JWT tokens

### Profile Management
- `GET /auth/api/profile/` - Get current user's profile
- `PATCH /auth/api/profile/` - Update current user's profile
- `POST /auth/api/profile/image/` - Upload profile image
- `GET /auth/api/profile/{user_id}/` - Get public profile

### Artist Dashboard
- `GET /auth/api/artist/dashboard/` - Artist dashboard statistics

## Models

### User Model (Extended AbstractUser)
- `user_type` - 'artist' or 'user'
- `phone` - Phone number
- `profile_image` - Profile picture
- `bio` - User biography
- `location` - User location
- `website` - Personal website URL
- `instagram_handle` - Instagram username
- `twitter_handle` - Twitter username
- `is_verified` - Verified artist status
- `artist_since` - When user became an artist

### Related Models
- `Artwork` - Artist artwork listings
- `Order` - Purchase orders
- `Transaction` - Payment transactions
- `Wishlist` - User saved artworks
- `Follow` - User follow relationships
- `Like` - Artwork likes
- `Comment` - Artwork comments

## Setup Instructions

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install django djangorestframework
   pip install djangorestframework-simplejwt
   pip install django-cors-headers
   pip install pillow  # For image handling
   ```

3. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Environment Variables
Create a `.env` file in the root directory:
```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

## CORS Configuration
Configured to allow requests from:
- `http://localhost:3000` (Next.js frontend)
- `http://127.0.0.1:3000`

## Media Files
- Profile images stored in `media/profiles/`
- Artwork images stored in `media/artworks/images/`
- Served at `/media/` in development

## Status
- ✅ Phase 1 (Authentication) - Complete
- ✅ Phase 2 (Profile Management) - Complete
- 🚧 Phase 3 (Enhanced Features) - In Progress