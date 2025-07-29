from graphene import relay
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from social_django import models as social_models

from .. import types

User = get_user_model()


class UserNode(DjangoObjectType):
    """Relay Node for User model."""
    
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email", 
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
        )
        interfaces = [relay.Node]


class SocialNode(types.SocialType):

    class Meta:
        model = social_models.UserSocialAuth
        fields = (
            "id",
            "user", 
            "provider",
            "uid",
            "extra_data",
            "created",
            "modified",
        )
        interfaces = [relay.Node]
        filter_fields = {
            "uid": ["exact", "in"],
            "provider": ["exact", "in"],
        }
