INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "social_django",
    "graphene_django",
    "django_filters",
]

GRAPHENE = {
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
    ],
}

AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

GRAPHQL_JWT = {
    "JWT_VERIFY_EXPIRATION": False,
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    },
}

SECRET_KEY = "test"

# Social Auth settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "test_key"
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "test_secret"

# Social Auth Pipeline
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

# Note: AUTHENTICATION_BACKENDS already defined above
