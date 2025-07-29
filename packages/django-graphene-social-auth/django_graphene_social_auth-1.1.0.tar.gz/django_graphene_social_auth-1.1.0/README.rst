Django GraphQL Social Auth
==========================

`Python Social Auth`_ support for `Django GraphQL`_

.. _Python Social Auth: https://python-social-auth.readthedocs.io/
.. _Django GraphQL: https://github.com/graphql-python/graphene-django

🚀 **Production-Ready** social authentication for GraphQL APIs with comprehensive error handling, logging, and security features.

Features
--------

* 🔐 **Session & JWT Authentication** - Support for both session-based and JWT token authentication
* 🛡️ **Enhanced Security** - Built-in rate limiting, input validation, and comprehensive error handling  
* 📊 **Production Monitoring** - Detailed logging and error tracking for production environments
* 🔧 **Easy Integration** - Simple GraphQL mutations with extensive documentation
* 🌐 **Multiple Providers** - Support for Google, Facebook, GitHub, Twitter, LinkedIn, Apple, and more
* 📚 **Comprehensive Docs** - Complete setup guides and troubleshooting documentation

Dependencies
------------

* Python ≥ 3.8
* Django ≥ 3.2
* graphene-django ≥ 3.0.0
* social-auth-app-django ≥ 5.0.0

Installation
------------

Install from PyPI:

.. code:: sh

    pip install django-graphene-social-auth

Quick Start
-----------

1. **Add to Django settings:**

.. code:: python

    INSTALLED_APPS = [
        # ... your apps
        'social_django',
        'graphene_django',
        # ... your apps  
    ]

    AUTHENTICATION_BACKENDS = [
        'social_core.backends.google.GoogleOAuth2',
        'social_core.backends.facebook.FacebookOAuth2',
        # ... other backends
        'django.contrib.auth.backends.ModelBackend',
    ]

    # Configure your social providers
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'your-google-client-id'
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'your-google-client-secret'

2. **Run migrations:**

.. code:: sh

    python manage.py migrate

3. **Add to your GraphQL schema:**

.. code:: python

    import graphene
    import graphql_social_auth

    class Mutations(graphene.ObjectType):
        # For session-based authentication
        social_auth = graphql_social_auth.SocialAuth.Field()
        
        # For JWT authentication (requires django-graphql-jwt)
        # social_auth = graphql_social_auth.SocialAuthJWT.Field()

Usage Examples
--------------

**GraphQL Mutation (Session Authentication):**

.. code:: graphql

    mutation SocialAuth($provider: String!, $accessToken: String!) {
      socialAuth(provider: $provider, accessToken: $accessToken) {
        success
        errors
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

**GraphQL Mutation (JWT Authentication):**

.. code:: graphql

    mutation SocialAuthJWT($provider: String!, $accessToken: String!) {
      socialAuth(provider: $provider, accessToken: $accessToken) {
        success
        errors
        token
        refreshToken
        social {
          uid
        }
      }
    }

**Variables:**

.. code:: json

    {
      "provider": "google-oauth2",
      "accessToken": "your-oauth-access-token"
    }

Supported Providers
-------------------

* **Google** - ``google-oauth2``
* **Facebook** - ``facebook``  
* **GitHub** - ``github``
* **Twitter** - ``twitter``
* **LinkedIn** - ``linkedin-oauth2``
* **Apple** - ``apple-id``
* **Discord** - ``discord``
* **Microsoft** - ``microsoft-graph``

For complete provider setup instructions, see the `Authentication backend list`_.

.. _Authentication backend list: https://python-social-auth.readthedocs.io/en/latest/backends/index.html

Production Setup
----------------

For production deployment with security best practices, monitoring, and troubleshooting guides, see:

* 📖 `Production Setup Guide <PRODUCTION_GUIDE.md>`_
* 🔧 `Troubleshooting Guide <TROUBLESHOOTING.md>`_  
* ⚙️ `Example Settings <example_settings.py>`_

Error Handling
--------------

The package provides comprehensive error handling with specific error types:

.. code:: python

    # Example error response
    {
      "data": {
        "socialAuth": {
          "success": false,
          "errors": ["Provider 'invalid-provider' not found or not configured"],
          "social": null,
          "user": null
        }
      }
    }

Common error types:

* ``PROVIDER_NOT_FOUND`` - Invalid or unconfigured provider
* ``INVALID_TOKEN`` - Expired or invalid access token  
* ``AUTH_FAILED`` - Authentication process failed
* ``RATE_LIMIT_EXCEEDED`` - Too many requests
* ``USER_CREATION_FAILED`` - User creation error

JWT Authentication
------------------

For JSON Web Token (JWT) authentication, install the JWT extension:

.. code:: sh

    pip install 'django-graphene-social-auth[jwt]'

Configure JWT in your settings (see ``example_settings.py`` for complete configuration):

.. code:: python

    import datetime
    
    GRAPHQL_JWT = {
        'JWT_EXPIRATION_DELTA': datetime.timedelta(minutes=60),
        'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
        'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    }

Use ``SocialAuthJWT`` instead of ``SocialAuth``:

.. code:: python

    import graphene
    import graphql_social_auth

    class Mutations(graphene.ObjectType):
        social_auth = graphql_social_auth.SocialAuthJWT.Field()

Relay Support
-------------

Complete support for `Relay`_:

.. _Relay: https://facebook.github.io/relay/

.. code:: python

    import graphene
    import graphql_social_auth

    class Mutations(graphene.ObjectType):
        social_auth = graphql_social_auth.relay.SocialAuth.Field()

Relay mutations accept input arguments:

.. code:: graphql

    mutation SocialAuth($input: SocialAuthInput!) {
      socialAuth(input: $input) {
        social {
          uid
        }
      }
    }

Customization
-------------

Customize the ``SocialAuth`` behavior by subclassing ``SocialAuthMutation``:

.. code:: python

    import graphene
    import graphql_social_auth
    from myapp.types import UserType

    class CustomSocialAuth(graphql_social_auth.SocialAuthMutation):
        user = graphene.Field(UserType)

        @classmethod
        def resolve(cls, root, info, social, **kwargs):
            # Custom logic here
            return cls(
                social=social,
                user=social.user,
                success=True,
                errors=[]
            )

Contributing
------------

We welcome contributions! Please see our GitHub repository for:

* 🐛 `Issue tracking <https://github.com/Ademic2022/django-graphene-social-auth/issues>`_
* 💡 `Feature requests <https://github.com/Ademic2022/django-graphene-social-auth/issues/new>`_
* 📝 `Pull requests <https://github.com/Ademic2022/django-graphene-social-auth/pulls>`_

License
-------

This project is licensed under the MIT License - see the `LICENSE <LICENSE>`_ file for details.

Acknowledgments
---------------

This package is a maintained fork of the original `django-graphql-social-auth`_ by `@flavors`_. 

Special thanks to `@omab`_ for `Python Social Auth`_.

.. _django-graphql-social-auth: https://github.com/flavors/django-graphql-social-auth/
.. _@flavors: https://github.com/flavors
.. _@omab: https://github.com/omab
.. _Python Social Auth: https://python-social-auth.readthedocs.io/
