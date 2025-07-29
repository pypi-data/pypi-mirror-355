from graphene.types.generic import GenericScalar
from graphene_django.types import DjangoObjectType
from django.contrib.auth import get_user_model
from social_django import models as social_models

from .utils import dashed_to_camel

User = get_user_model()


class CamelJSON(GenericScalar):

    @classmethod
    def serialize(cls, value):
        return dashed_to_camel(value)

    class Meta:
        name = "SocialCamelJSON"


class UserType(DjangoObjectType):
    """GraphQL type for User model."""
    
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


class SocialType(DjangoObjectType):
    extra_data = CamelJSON()

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

    def resolve_extra_data(self, info, **kwargs):
        self.extra_data.pop("access_token", None)
        return self.extra_data
