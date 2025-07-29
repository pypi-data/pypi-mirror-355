import graphene
import logging

from . import mixins, types
from .decorators import social_auth
from .exceptions import GraphQLSocialAuthError

logger = logging.getLogger(__name__)


class SocialAuthMutation(mixins.SocialAuthMixin, graphene.Mutation):
    """Base Social Auth Mutation with error handling"""
    
    social = graphene.Field(types.SocialType)
    success = graphene.Boolean(default_value=True)
    errors = graphene.List(graphene.String)

    class Meta:
        abstract = True

    class Arguments:
        provider = graphene.String(
            required=True,
            description="Social provider name (e.g., 'google-oauth2', 'facebook', 'github')"
        )
        access_token = graphene.String(
            required=True,
            description="OAuth access token from the social provider"
        )

    @classmethod
    @social_auth
    def mutate(cls, root, info, social, **kwargs):
        try:
            result = cls.resolve(root, info, social, **kwargs)
            if result is None:
                result = cls()
            
            # Ensure success and errors are set
            if not hasattr(result, 'success'):
                result.success = True
            if not hasattr(result, 'errors'):
                result.errors = []
                
            return result
        except GraphQLSocialAuthError as e:
            logger.error(f"Social auth error in {cls.__name__}: {e}")
            return cls(
                success=False,
                errors=[str(e)],
                social=None
            )
        except Exception as e:
            logger.error(f"Unexpected error in {cls.__name__}: {e}")
            return cls(
                success=False,
                errors=["An unexpected error occurred. Please try again."],
                social=None
            )


class SocialAuth(mixins.ResolveMixin, SocialAuthMutation):
    """Social Auth Mutation for session-based authentication"""
    
    user = graphene.Field(types.UserType)
    
    class Meta:
        description = "Authenticate user with social provider and create/login session"


class SocialAuthJWT(mixins.JSONWebTokenMixin, SocialAuthMutation):
    """Social Auth for JSON Web Token (JWT) authentication"""
    
    token = graphene.String(description="JWT access token")
    refresh_token = graphene.String(description="JWT refresh token (if available)")
    
    class Meta:
        description = "Authenticate user with social provider and return JWT tokens"
