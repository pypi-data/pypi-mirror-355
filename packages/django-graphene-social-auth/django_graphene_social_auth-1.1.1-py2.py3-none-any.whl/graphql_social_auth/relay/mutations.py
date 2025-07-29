import graphene
import logging

from .. import mixins, mutations
from ..decorators import social_auth
from ..exceptions import GraphQLSocialAuthError
from . import nodes

logger = logging.getLogger(__name__)


class SocialAuthMutation(mixins.SocialAuthMixin,
                         graphene.relay.ClientIDMutation):

    social = graphene.Field(nodes.SocialNode)
    success = graphene.Boolean(default_value=True)
    errors = graphene.List(graphene.String)

    class Meta:
        abstract = True

    class Input(mutations.SocialAuthMutation.Arguments):
        """Social Auth Input"""

    @classmethod
    @social_auth
    def mutate_and_get_payload(cls, root, info, social, **kwargs):
        try:
            result = cls.resolve(root, info, social, **kwargs)
            if result is None:
                result = cls()

            # Ensure success and errors are set
            if not hasattr(result, "success"):
                result.success = True
            if not hasattr(result, "errors"):
                result.errors = []

            return result
        except (ImportError, ModuleNotFoundError):
            # Let import errors bubble up as GraphQL errors for dependency issues
            raise
        except GraphQLSocialAuthError as e:
            logger.error(f"Relay social auth error in {cls.__name__}: {e}")
            return cls(success=False, errors=[str(e)], social=None)
        except Exception as e:
            logger.error(f"Relay unexpected error in {cls.__name__}: {e}")
            return cls(
                success=False,
                errors=["An unexpected error occurred. Please try again."],
                social=None,
            )


class SocialAuth(mixins.ResolveMixin, SocialAuthMutation):
    """Social Auth Mutation for Relay"""


class SocialAuthJWT(mixins.JSONWebTokenMixin, SocialAuthMutation):
    """Social Auth for JSON Web Token (JWT)"""
