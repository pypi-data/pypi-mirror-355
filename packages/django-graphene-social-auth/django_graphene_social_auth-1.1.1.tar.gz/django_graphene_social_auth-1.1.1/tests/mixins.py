import sys
from unittest.mock import patch

from .decorators import social_auth_mock


class SocialAuthMixin:

    @social_auth_mock
    @patch("graphql_social_auth.decorators._do_login")
    def test_social_auth(self, *args):
        response = self.execute(
            {
                "provider": "google-oauth2",
                "accessToken": "-token-",
            }
        )

        social = response.data["socialAuth"]["social"]
        self.assertEqual("test", social["uid"])


class SocialAuthJWTMixin:

    @social_auth_mock
    @patch("graphql_jwt.shortcuts.get_token", return_value="test-token")
    def test_social_auth(self, get_token_mock, *args):
        response = self.execute(
            {
                "provider": "google-oauth2",
                "accessToken": "-token-",
            }
        )

        if response.errors:
            print("GraphQL Errors:", response.errors)
            
        self.assertIsNone(response.errors, "Unexpected GraphQL errors")
        self.assertIsNotNone(response.data, "Response data is None")
        self.assertIsNotNone(response.data.get("socialAuth"), "socialAuth is None")
        
        social = response.data["socialAuth"]["social"]
        self.assertEqual("test", social["uid"])
        self.assertEqual("test-token", response.data["socialAuth"]["token"])

    @social_auth_mock
    @patch.dict(sys.modules, {"graphql_jwt.shortcuts": None})
    def test_social_auth_import_error(self, *args):
        response = self.execute(
            {
                "provider": "google-oauth2",
                "accessToken": "-token-",
            }
        )

        self.assertTrue(response.errors)
        self.assertIsNone(response.data["socialAuth"])
