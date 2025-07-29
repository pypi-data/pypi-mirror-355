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


def psa(f):
    @wraps(f)
    def wrapper(cls, root, info, provider, access_token, **kwargs):
        strategy = load_strategy(info.context)

        try:
            backend = load_backend(strategy, provider, redirect_uri=None)
        except MissingBackend:
            raise exceptions.GraphQLSocialAuthError(_("Provider not found"))

        if info.context.user.is_authenticated:
            authenticated_user = info.context.user
        else:
            authenticated_user = None

        user = backend.do_auth(access_token, user=authenticated_user)

        if user is None:
            raise exceptions.InvalidTokenError(_("Invalid token"))

        user_model = strategy.storage.user.user_model()

        if not isinstance(user, user_model):
            msg = _("`{}` is not a user instance").format(type(user).__name__)
            raise exceptions.DoAuthError(msg, user)

        if not issubclass(cls, mixins.JSONWebTokenMixin):
            _do_login(backend, user, user.social_user)

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
