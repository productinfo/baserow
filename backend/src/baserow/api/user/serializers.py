from typing import Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from rest_framework import exceptions, serializers
from rest_framework.request import Request
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import TokenError

from baserow.api.groups.invitations.serializers import UserGroupInvitationSerializer
from baserow.api.user.jwt import get_user_from_jwt_token
from baserow.api.user.registries import user_data_registry
from baserow.api.user.validators import language_validation, password_validation
from baserow.core.models import Template
from baserow.core.user.handler import UserHandler
from baserow.core.user.utils import normalize_email_address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    language = serializers.CharField(
        source="profile.language",
        required=False,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "username",
            "password",
            "is_staff",
            "id",
            "language",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "is_staff": {"read_only": True},
            "id": {"read_only": True},
        }


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Serializer that exposes only fields that can be shared
    about the user for the whole group.
    """

    class Meta:
        model = User
        fields = ("id", "username", "first_name")
        extra_kwargs = {
            "id": {"read_only": True},
        }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=150)
    email = serializers.EmailField(
        help_text="The email address is also going to be the username."
    )
    password = serializers.CharField(validators=[password_validation])
    language = serializers.CharField(
        required=False,
        default=settings.LANGUAGE_CODE,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )
    authenticate = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Indicates whether an authentication token should be generated and "
        "be included in the response.",
    )
    group_invitation_token = serializers.CharField(
        required=False,
        help_text="If provided and valid, the user accepts the group invitation and "
        "will have access to the group after signing up.",
    )
    template_id = serializers.PrimaryKeyRelatedField(
        required=False,
        default=None,
        queryset=Template.objects.all(),
        help_text="The id of the template that must be installed after creating the "
        "account. This only works if the `group_invitation_token` param is not "
        "provided.",
    )


class AccountSerializer(serializers.Serializer):
    """
    This serializer must be kept in sync with `UserSerializer`.
    """

    first_name = serializers.CharField(min_length=2, max_length=150)
    language = serializers.CharField(
        source="profile.language",
        required=False,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )


class SendResetPasswordEmailBodyValidationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="The email address of the user that has requested a password reset."
    )
    base_url = serializers.URLField(
        help_text="The base URL where the user can reset his password. The reset "
        "token is going to be appended to the base_url (base_url "
        "'/token')."
    )


class ResetPasswordBodyValidationSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(validators=[password_validation])


class ChangePasswordBodyValidationSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validation])


class DeleteUserBodyValidationSerializer(serializers.Serializer):
    password = serializers.CharField()


class NormalizedEmailField(serializers.EmailField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return normalize_email_address(data)


def get_all_user_data_serialized(
    user: AbstractUser, request: Optional[Request] = None
) -> Dict:
    """
    Update the payload with the additional user data that must be added.
    The `user_data_registry` contains instances that want to add additional
    information to this payload.

    :param user: The user for which the data must be serialized.
    :param request: The request that is used to generate the data.
    :return: A dictionary with the serialized data for the user.
    """

    return {
        "user": UserSerializer(user, context={"request": request}).data,
        **user_data_registry.get_all_user_data(user, request),
    }


class TokenObtainPairWithUserSerializer(TokenObtainPairSerializer):
    email = NormalizedEmailField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = NormalizedEmailField(required=False)

    def validate(self, attrs):
        """
        This serializer is only used by the ObtainJSONWebToken view which is only used
        to generate a new token. When that happens we want to update the user's last
        login timestamp.
        """

        # this permits to use "email" as field in the serializer giving us compatibility
        # with the TokenObtainPairSerializer that expects "username" instead.
        if not attrs.get(self.username_field):
            email = attrs.get("email")
            if not email:
                raise serializers.ValidationError({"email": "This field is required."})
            attrs[self.username_field] = email

        try:
            validated_data = super().validate(attrs)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError(
                {"detail": exc.detail, "error": "ERROR_INVALID_CREDENTIALS"}, exc.code
            )

        validated_data.update(
            **get_all_user_data_serialized(self.user, self.context["request"])
        )
        UserHandler().user_signed_in(self.user)

        return validated_data


class TokenRefreshWithUserSerializer(TokenRefreshSerializer):

    default_error_messages = TokenObtainPairSerializer.default_error_messages

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        access_token = validated_data["access"]
        try:
            user = get_user_from_jwt_token(access_token)
        except KeyError:
            raise exceptions.AuthenticationFailed(
                {"detail": "Token is invalid", "error": "ERROR_INVALID_TOKEN"}
            )
        except TokenError:
            # can happen if the user has been deleted/disabled in the meantime
            raise exceptions.AuthenticationFailed(
                {
                    "detail": self.error_messages["no_active_account"],
                    "error": "ERROR_NO_ACTIVE_ACCOUNT",
                }
            )
        validated_data.update(
            **get_all_user_data_serialized(user, self.context["request"])
        )
        return validated_data


class DashboardSerializer(serializers.Serializer):
    group_invitations = UserGroupInvitationSerializer(many=True)
