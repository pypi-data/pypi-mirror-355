# Django GraphQL Social Auth - Production Setup Guide

This guide addresses common production issues and provides a complete setup walkthrough.

## Prerequisites

- Python ≥ 3.8
- Django ≥ 3.2
- django-graphene-social-auth
- social-auth-app-django

## Installation

```bash
pip install django-graphene-social-auth
```

## Complete Django Configuration

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ... your other apps
    'social_django',  # Required for social auth
    'graphene_django',  # Required for GraphQL
    # ... your other apps
]
```

### 2. Authentication Backends

Add social auth backends to your settings:

```python
AUTHENTICATION_BACKENDS = [
    # Social auth backends
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.github.GithubOAuth2',
    # Add other backends as needed
    
    # Keep Django's default backend last
    'django.contrib.auth.backends.ModelBackend',
]
```

### 3. Database Migration

Run migrations to create social auth tables:

```bash
python manage.py migrate
```

### 4. URL Configuration

Add social auth URLs to your main urls.py:

```python
from django.urls import path, include

urlpatterns = [
    # ... your other URLs
    path('auth/', include('social_django.urls', namespace='social')),
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    # ... your other URLs
]
```

### 5. Social Auth Settings

Configure your social providers:

```python
# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'your-google-client-id'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'your-google-client-secret'

# Facebook
SOCIAL_AUTH_FACEBOOK_KEY = 'your-facebook-app-id'
SOCIAL_AUTH_FACEBOOK_SECRET = 'your-facebook-app-secret'

# GitHub
SOCIAL_AUTH_GITHUB_KEY = 'your-github-client-id'
SOCIAL_AUTH_GITHUB_SECRET = 'your-github-client-secret'

# Optional: Enable JSON field for PostgreSQL
SOCIAL_AUTH_JSONFIELD_ENABLED = True

# Optional: Specify redirect URLs
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/login-error/'
```

### 6. GraphQL Schema Setup

```python
import graphene
import graphql_social_auth

class Query(graphene.ObjectType):
    # Your queries here
    pass

class Mutations(graphene.ObjectType):
    # For session-based authentication
    social_auth = graphql_social_auth.SocialAuth.Field()
    
    # For JWT authentication (if using JWT)
    # social_auth = graphql_social_auth.SocialAuthJWT.Field()

schema = graphene.Schema(query=Query, mutation=Mutations)
```

## Common Production Issues and Solutions

### Issue 1: "No backend found" Error

**Problem**: Backend not properly configured or missing from AUTHENTICATION_BACKENDS.

**Solution**: 
- Ensure the backend is listed in AUTHENTICATION_BACKENDS
- Verify the provider name matches exactly (case-sensitive)
- Check that social_django is in INSTALLED_APPS

### Issue 2: "Invalid token" Error

**Problem**: Access token is expired or invalid.

**Solution**:
- Implement token refresh mechanism on frontend
- Validate tokens before sending to GraphQL
- Add proper error handling

### Issue 3: Database Migration Issues

**Problem**: Missing social auth tables.

**Solution**:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue 4: CORS Issues in Production

**Problem**: Cross-origin requests blocked.

**Solution**:
```python
# Install django-cors-headers
pip install django-cors-headers

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'corsheaders',
    # ... other apps
]

# Add to MIDDLEWARE
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]

# Configure CORS
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

### Issue 5: Missing User Data

**Problem**: User profile not properly populated.

**Solution**: Customize the pipeline:
```python
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)
```

## Example GraphQL Mutations

### Session Authentication

```graphql
mutation SocialAuth($provider: String!, $accessToken: String!) {
  socialAuth(provider: $provider, accessToken: $accessToken) {
    social {
      uid
      extraData
    }
    user {
      id
      username
      email
    }
  }
}
```

### JWT Authentication (if using JWT extension)

```graphql
mutation SocialAuthJWT($provider: String!, $accessToken: String!) {
  socialAuth(provider: $provider, accessToken: $accessToken) {
    social {
      uid
    }
    token
    refreshToken
  }
}
```

## Production Environment Variables

Create a `.env` file or set environment variables:

```bash
# Social Auth Keys
GOOGLE_OAUTH2_KEY=your_google_client_id
GOOGLE_OAUTH2_SECRET=your_google_client_secret
FACEBOOK_KEY=your_facebook_app_id
FACEBOOK_SECRET=your_facebook_app_secret

# Django Settings
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

Load in settings.py:
```python
import os
from decouple import config  # pip install python-decouple

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_OAUTH2_SECRET')
```

## Troubleshooting

### Enable Debug Logging

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'social_auth.log',
        },
    },
    'loggers': {
        'social_core': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Test Authentication Flow

```python
# In Django shell
python manage.py shell

from social_django.models import UserSocialAuth
from django.contrib.auth.models import User

# Check if social auth records exist
UserSocialAuth.objects.all()

# Check users
User.objects.all()
```

## Support

- GitHub Issues: https://github.com/Ademic2022/django-graphene-social-auth/issues
- PyPI: https://pypi.org/project/django-graphene-social-auth/
- Social Auth Documentation: https://python-social-auth.readthedocs.io/
