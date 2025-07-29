# Example Django settings for django-graphene-social-auth
# Copy and modify these settings for your Django project

import os
from decouple import config  # pip install python-decouple

# =============================================================================
# BASIC DJANGO SETTINGS
# =============================================================================

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")]
)

# =============================================================================
# INSTALLED APPS - Add these to your INSTALLED_APPS
# =============================================================================

DJANGO_GRAPHENE_SOCIAL_AUTH_APPS = [
    "social_django",  # Required for social authentication
    "graphene_django",  # Required for GraphQL
    "corsheaders",  # Optional: for CORS support
]

# Add to your existing INSTALLED_APPS:
# INSTALLED_APPS = [
#     # ... your existing apps
#     'social_django',
#     'graphene_django',
#     # ... your other apps
# ]

# =============================================================================
# MIDDLEWARE - Add these to your MIDDLEWARE
# =============================================================================

DJANGO_GRAPHENE_SOCIAL_AUTH_MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Optional: for CORS
    "social_django.middleware.SocialAuthExceptionMiddleware",  # Optional: for error handling
]

# =============================================================================
# AUTHENTICATION BACKENDS
# =============================================================================

AUTHENTICATION_BACKENDS = [
    # Social auth backends - add the ones you need
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.facebook.FacebookOAuth2",
    "social_core.backends.twitter.TwitterOAuth",
    "social_core.backends.github.GithubOAuth2",
    "social_core.backends.linkedin.LinkedinOAuth2",
    "social_core.backends.apple.AppleIdAuth",
    "social_core.backends.discord.DiscordOAuth2",
    "social_core.backends.microsoft.MicrosoftOAuth2",
    # Keep Django's default backend last
    "django.contrib.auth.backends.ModelBackend",
]

# =============================================================================
# GRAPHENE SETTINGS
# =============================================================================

GRAPHENE = {
    "SCHEMA": "your_project.schema.schema",  # Update this to your schema path
    "MIDDLEWARE": [
        # Add any GraphQL middleware here
    ],
}

# =============================================================================
# SOCIAL AUTH SETTINGS
# =============================================================================

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config("GOOGLE_OAUTH2_KEY", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config("GOOGLE_OAUTH2_SECRET", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Facebook
SOCIAL_AUTH_FACEBOOK_KEY = config("FACEBOOK_KEY", default="")
SOCIAL_AUTH_FACEBOOK_SECRET = config("FACEBOOK_SECRET", default="")
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "id,name,email"}

# GitHub
SOCIAL_AUTH_GITHUB_KEY = config("GITHUB_KEY", default="")
SOCIAL_AUTH_GITHUB_SECRET = config("GITHUB_SECRET", default="")
SOCIAL_AUTH_GITHUB_SCOPE = ["user:email"]

# Twitter
SOCIAL_AUTH_TWITTER_KEY = config("TWITTER_KEY", default="")
SOCIAL_AUTH_TWITTER_SECRET = config("TWITTER_SECRET", default="")

# LinkedIn
SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = config("LINKEDIN_KEY", default="")
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = config("LINKEDIN_SECRET", default="")
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ["r_liteprofile", "r_emailaddress"]
SOCIAL_AUTH_LINKEDIN_OAUTH2_FIELD_SELECTORS = ["email-address"]

# Apple
SOCIAL_AUTH_APPLE_ID_CLIENT = config("APPLE_CLIENT_ID", default="")
SOCIAL_AUTH_APPLE_ID_TEAM = config("APPLE_TEAM_ID", default="")
SOCIAL_AUTH_APPLE_ID_KEY = config("APPLE_KEY_ID", default="")
SOCIAL_AUTH_APPLE_ID_SECRET = config("APPLE_SECRET", default="")

# =============================================================================
# SOCIAL AUTH CONFIGURATION
# =============================================================================

# Database settings
SOCIAL_AUTH_JSONFIELD_ENABLED = True  # Enable JSON fields for PostgreSQL

# URLs and redirects
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/"
SOCIAL_AUTH_LOGIN_ERROR_URL = "/login-error/"
SOCIAL_AUTH_URL_NAMESPACE = "social"

# User model and creation
SOCIAL_AUTH_USER_MODEL = "auth.User"  # Default Django user model
SOCIAL_AUTH_CREATE_USERS = True
SOCIAL_AUTH_IMMUTABLE_USER_FIELDS = ["username"]

# Session settings
SOCIAL_AUTH_SESSION_EXPIRATION = False

# Pipeline configuration
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

# =============================================================================
# DJANGO-GRAPHENE-SOCIAL-AUTH SPECIFIC SETTINGS
# =============================================================================

# Rate limiting (optional)
SOCIAL_AUTH_RATE_LIMIT_ENABLED = True
SOCIAL_AUTH_RATE_LIMIT_ATTEMPTS = 10  # attempts per window
SOCIAL_AUTH_RATE_LIMIT_WINDOW = 60  # seconds

# Error handling
SOCIAL_AUTH_RAISE_EXCEPTIONS = False  # Set to True for development debugging

# =============================================================================
# JWT SETTINGS (if using django-graphql-jwt)
# =============================================================================

# Uncomment and configure if using JWT authentication
# import datetime
#
# GRAPHQL_JWT = {
#     'JWT_ALGORITHM': 'HS256',
#     'JWT_AUDIENCE': None,
#     'JWT_ISSUER': None,
#     'JWT_LEEWAY': 0,
#     'JWT_SECRET_KEY': SECRET_KEY,
#     'JWT_VERIFY_EXPIRATION': True,
#     'JWT_EXPIRATION_DELTA': datetime.timedelta(minutes=60),
#     'JWT_ALLOW_REFRESH': True,
#     'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
#     'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
# }

# =============================================================================
# CORS SETTINGS (if using django-cors-headers)
# =============================================================================

# Configure CORS for your frontend domains
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",  # Alternative localhost
    # Add your production domains here
    # "https://yourdomain.com",
    # "https://www.yourdomain.com",
]

CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/social_auth.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG" if DEBUG else "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "graphql_social_auth": {
            "handlers": ["file", "console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "social_core": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "social_django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Make sure to run migrations after installing social_django:
# python manage.py migrate

# =============================================================================
# SECURITY SETTINGS FOR PRODUCTION
# =============================================================================

if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
