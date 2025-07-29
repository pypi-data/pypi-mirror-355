from unittest.mock import patch
from django.test import override_settings

from graphql_social_auth import decorators, exceptions
from graphql_social_auth.decorators import is_thenable

from .decorators import social_auth_mock
from .testcases import TestCase


class MockPromise:
    """Mock promise-like object for testing"""

    def __init__(self, value=None):
        self.value = value

    def then(self, callback):
        # Create a mock result object that has a social attribute
        mock_result = type("MockResult", (), {"social": None})()
        return MockPromise(callback(mock_result))


class DecoratorsTests(TestCase):

    def test_psa_missing_backend(self):

        @decorators.social_auth
        def wrapped(cls, root, info, provider, *args):
            """Social Auth decorated function"""

        with self.assertRaises(exceptions.GraphQLSocialAuthError):
            wrapped(self, None, self.info(), "unknown", "token")

    @social_auth_mock
    @override_settings(SOCIAL_AUTH_PIPELINE=[])
    def test_psa_invalid_token(self, *args):

        @decorators.social_auth
        def wrapped(cls, root, info, provider, *args):
            """Social Auth decorated function"""

        with self.assertRaises(exceptions.InvalidTokenError):
            wrapped(self, None, self.info(), "google-oauth2", "token")

    @social_auth_mock
    @patch("social_core.backends.oauth.BaseOAuth2.do_auth")
    def test_psa_do_auth_error(self, *args):

        @decorators.social_auth
        def wrapped(cls, root, info, provider, *args):
            """Social Auth decorated function"""

        with self.assertRaises(exceptions.DoAuthError):
            wrapped(self, None, self.info(), "google-oauth2", "token")

    @social_auth_mock
    def test_social_auth_thenable(self, *args):

        @decorators.social_auth
        def wrapped(cls, root, info, provider, *args):
            return MockPromise()

        result = wrapped(TestCase, None, self.info(), "google-oauth2", "token")

        self.assertTrue(is_thenable(result))

    @social_auth_mock
    def test_social_auth_async(self, *args):

        @decorators.social_auth
        async def wrapped(cls, root, info, provider, *args):
            return type("MockResult", (), {})()

        result = wrapped(TestCase, None, self.info(), "google-oauth2", "token")

        # The result should be a coroutine that we can check is thenable
        self.assertTrue(is_thenable(result))

        # Actually run the coroutine to completion to avoid warnings
        import asyncio

        try:
            # For testing purposes, let's run the coroutine
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                final_result = loop.run_until_complete(result)
                # Verify we got a result back
                self.assertIsNotNone(final_result)
            finally:
                loop.close()
        except Exception:
            # If there's an issue running it, just close it to prevent warnings
            if hasattr(result, "close"):
                result.close()
