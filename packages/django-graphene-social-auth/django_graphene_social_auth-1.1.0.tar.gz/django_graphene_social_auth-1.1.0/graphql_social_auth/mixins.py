import graphene
import logging

logger = logging.getLogger(__name__)


class SocialAuthMixin:
    """Base mixin for social authentication mutations"""

    @classmethod
    def __init_subclass_with_meta__(cls, name=None, **options):
        assert getattr(cls, 'resolve', None), (
            '{name}.resolve method is required in a SocialAuthMutation.'
        ).format(name=name or cls.__name__)

        super().__init_subclass_with_meta__(name=name, **options)


class ResolveMixin:
    """Mixin for basic session-based authentication"""

    @classmethod
    def resolve(cls, root, info, social, **kwargs):
        """Resolve method for session-based auth"""
        logger.info(f"Session auth successful for user {social.user.id}")
        return cls(
            social=social,
            user=social.user,
            success=True,
            errors=[]
        )


class JSONWebTokenMixin:
    """Mixin for JWT-based authentication"""
    
    token = graphene.String()
    refresh_token = graphene.String()

    @classmethod
    def resolve(cls, root, info, social, **kwargs):
        """Resolve method for JWT auth"""
        try:
            from graphql_jwt.shortcuts import get_token
            from graphql_jwt.settings import jwt_settings
            
            token = get_token(social.user)
            
            # Try to create refresh token if available
            refresh_token = None
            try:
                if jwt_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
                    from graphql_jwt.refresh_token.shortcuts import create_refresh_token
                    refresh_token_obj = create_refresh_token(social.user)
                    refresh_token = refresh_token_obj.token
                    logger.info(f"Refresh token created for user {social.user.id}")
            except Exception as e:
                # Refresh tokens not available or error occurred
                logger.warning(f"Refresh token not available: {e}")
                refresh_token = None
            
            logger.info(f"JWT auth successful for user {social.user.id}")
            return cls(
                social=social,
                token=token,
                refresh_token=refresh_token,
                success=True,
                errors=[]
            )
            
        except ImportError:
            error_msg = (
                'django-graphql-jwt not installed or not properly configured.\n'
                "Use `pip install 'django-graphene-social-auth[jwt]'` "
                "and configure JWT settings in your Django settings."
            )
            logger.error(error_msg)
            raise ImportError(error_msg)
