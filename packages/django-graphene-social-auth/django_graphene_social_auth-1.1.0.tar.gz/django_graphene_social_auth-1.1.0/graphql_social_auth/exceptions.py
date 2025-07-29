
import logging

logger = logging.getLogger(__name__)


class GraphQLSocialAuthError(Exception):
    """Base exception for GraphQL Social Auth"""
    
    def __init__(self, message, error_code=None, extra_data=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'SOCIAL_AUTH_ERROR'
        self.extra_data = extra_data or {}
        logger.error(f"Social Auth Error: {message}", extra={
            'error_code': self.error_code,
            'extra_data': self.extra_data
        })


class InvalidTokenError(GraphQLSocialAuthError):
    """Raise when access token is invalid or expired"""
    
    def __init__(self, message="Invalid or expired access token", provider=None):
        super().__init__(
            message, 
            error_code='INVALID_TOKEN',
            extra_data={'provider': provider}
        )


class DoAuthError(GraphQLSocialAuthError):
    """Raise when authentication process fails"""

    def __init__(self, message, result=None, provider=None):
        super().__init__(
            message,
            error_code='AUTH_FAILED',
            extra_data={'provider': provider, 'result': str(result)}
        )
        self.result = result


class ProviderNotFoundError(GraphQLSocialAuthError):
    """Raise when social auth provider is not configured"""
    
    def __init__(self, provider):
        message = f"Provider '{provider}' not found or not configured"
        super().__init__(
            message,
            error_code='PROVIDER_NOT_FOUND',
            extra_data={'provider': provider}
        )


class UserCreationError(GraphQLSocialAuthError):
    """Raise when user creation fails"""
    
    def __init__(self, message="Failed to create user", provider=None):
        super().__init__(
            message,
            error_code='USER_CREATION_FAILED',
            extra_data={'provider': provider}
        )


class RateLimitError(GraphQLSocialAuthError):
    """Raise when rate limit is exceeded"""
    
    def __init__(self, message="Rate limit exceeded"):
        super().__init__(
            message,
            error_code='RATE_LIMIT_EXCEEDED'
        )
