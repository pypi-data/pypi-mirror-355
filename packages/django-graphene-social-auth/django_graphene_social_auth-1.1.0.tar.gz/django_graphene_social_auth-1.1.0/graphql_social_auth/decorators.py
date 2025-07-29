from functools import wraps
import asyncio
import inspect

from django.utils.translation import gettext_lazy as _

from social_core.exceptions import MissingBackend
from social_django.utils import load_backend, load_strategy
from social_django.views import _do_login

from . import exceptions, mixins


def is_thenable(obj):
    """Check if object is a thenable (has then method) or coroutine"""
    return (
        hasattr(obj, "then")
        and callable(getattr(obj, "then"))
        or asyncio.iscoroutine(obj)
        or inspect.isawaitable(obj)
    )


from functools import wraps
import asyncio
import inspect
import logging
import re

from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings

from social_core.exceptions import MissingBackend, AuthException
from social_django.utils import load_backend, load_strategy
from social_django.views import _do_login

from . import exceptions, mixins

logger = logging.getLogger(__name__)


def is_thenable(obj):
    """Check if object is a thenable (has then method) or coroutine"""
    return (
        hasattr(obj, "then")
        and callable(getattr(obj, "then"))
        or asyncio.iscoroutine(obj)
        or inspect.isawaitable(obj)
    )


def validate_provider(provider):
    """Validate provider name"""
    if not provider:
        raise exceptions.ProviderNotFoundError("Provider name is required")
    
    # Check if provider name is alphanumeric with hyphens/underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', provider):
        raise exceptions.ProviderNotFoundError(provider)
    
    return provider


def validate_access_token(access_token):
    """Validate access token format"""
    if not access_token:
        raise exceptions.InvalidTokenError("Access token is required")
    
    # Basic validation - tokens should be non-empty and reasonable length
    if len(access_token.strip()) < 10:
        raise exceptions.InvalidTokenError("Access token appears to be invalid")
    
    return access_token.strip()


def check_rate_limit(request, provider):
    """Simple rate limiting based on IP and provider"""
    rate_limit_enabled = getattr(settings, 'SOCIAL_AUTH_RATE_LIMIT_ENABLED', True)
    if not rate_limit_enabled:
        return
    
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Rate limit: 10 attempts per minute per IP per provider
    max_attempts = getattr(settings, 'SOCIAL_AUTH_RATE_LIMIT_ATTEMPTS', 10)
    window = getattr(settings, 'SOCIAL_AUTH_RATE_LIMIT_WINDOW', 60)  # seconds
    
    cache_key = f"social_auth_rate_limit:{ip}:{provider}"
    current_attempts = cache.get(cache_key, 0)
    
    if current_attempts >= max_attempts:
        logger.warning(f"Rate limit exceeded for IP {ip} and provider {provider}")
        raise exceptions.RateLimitError()
    
    # Increment counter
    cache.set(cache_key, current_attempts + 1, window)


def psa(f):
    @wraps(f)
    def wrapper(cls, root, info, provider, access_token, **kwargs):
        # Validate inputs
        provider = validate_provider(provider)
        access_token = validate_access_token(access_token)
        
        # Check rate limiting
        try:
            check_rate_limit(info.context, provider)
        except Exception as e:
            logger.warning(f"Rate limiting check failed: {e}")
            # Don't fail if rate limiting has issues, but log it
        
        # Load strategy and backend
        strategy = load_strategy(info.context)

        try:
            backend = load_backend(strategy, provider, redirect_uri=None)
        except MissingBackend as e:
            logger.error(f"Backend not found for provider: {provider}")
            raise exceptions.ProviderNotFoundError(provider)

        # Get authenticated user if available
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            authenticated_user = info.context.user
        else:
            authenticated_user = None

        # Perform authentication
        try:
            user = backend.do_auth(access_token, user=authenticated_user)
        except AuthException as e:
            logger.error(f"Authentication failed for provider {provider}: {e}")
            raise exceptions.InvalidTokenError(str(e), provider=provider)
        except Exception as e:
            logger.error(f"Unexpected error during auth for provider {provider}: {e}")
            raise exceptions.DoAuthError(
                "Authentication failed due to an unexpected error",
                result=str(e),
                provider=provider
            )

        if user is None:
            logger.warning(f"Authentication returned None for provider {provider}")
            raise exceptions.InvalidTokenError("Authentication failed", provider=provider)

        # Validate user type
        user_model = strategy.storage.user.user_model()
        if not isinstance(user, user_model):
            msg = f"`{type(user).__name__}` is not a user instance"
            logger.error(f"Invalid user type returned: {msg}")
            raise exceptions.DoAuthError(msg, user, provider=provider)

        # Handle login for non-JWT mixins
        if not issubclass(cls, mixins.JSONWebTokenMixin):
            try:
                _do_login(backend, user, user.social_user)
            except Exception as e:
                logger.error(f"Login failed for provider {provider}: {e}")
                # Don't fail the mutation, just log the error
                pass

        logger.info(f"Successful authentication for provider {provider}, user {user.id}")
        return f(cls, root, info, user.social_user, **kwargs)

    return wrapper


def social_auth(f):
    @psa
    @wraps(f)
    def wrapper(cls, root, info, social, **kwargs):
        def on_resolve(payload):
            payload.social = social
            return payload

        result = f(cls, root, info, social, **kwargs)

        if is_thenable(result):
            # Handle async/await or thenable objects
            if asyncio.iscoroutine(result):

                async def async_wrapper():
                    resolved = await result
                    return on_resolve(resolved)

                return async_wrapper()
            elif hasattr(result, "then"):
                # For promise-like objects, call then method
                return result.then(on_resolve)
        return on_resolve(result)

    return wrapper
