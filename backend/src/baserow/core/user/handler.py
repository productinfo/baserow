from datetime import timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from itsdangerous import URLSafeTimedSerializer

from baserow.core.auth_provider.handler import PasswordProviderHandler
from baserow.core.auth_provider.models import AuthProviderModel
from baserow.core.exceptions import (
    BaseURLHostnameNotAllowed,
    GroupInvitationEmailMismatch,
)
from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser, Template, UserLogEntry, UserProfile
from baserow.core.registries import plugin_registry
from baserow.core.signals import (
    before_user_deleted,
    user_deleted,
    user_permanently_deleted,
    user_restored,
    user_updated,
)
from baserow.core.trash.handler import TrashHandler

from .emails import (
    AccountDeleted,
    AccountDeletionCanceled,
    AccountDeletionScheduled,
    ResetPasswordEmail,
)
from .exceptions import (
    DeactivatedUserException,
    DisabledSignupError,
    InvalidPassword,
    PasswordDoesNotMatchValidation,
    ResetPasswordDisabledError,
    UserAlreadyExist,
    UserIsLastAdmin,
    UserNotFound,
)
from .utils import normalize_email_address

User = get_user_model()


class UserHandler:
    def get_active_user(
        self,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        exclude_users_scheduled_to_be_deleted: bool = False,
    ) -> AbstractUser:
        """
        Finds and returns a single active user instance based on the provided
        parameters.

        :param user_id: The user id of the user.
        :param email: The username, which is their email address, of the user.
        :param exclude_users_scheduled_to_be_deleted: If set to True, the user will
            not be returned if it is scheduled to be deleted.
        :raises ValueError: When neither a `user_id` or `email` has been
            provided.
        :raises UserNotFound: When the user with the provided parameters has not
            been found.
        :return: The requested user.
        """

        if not user_id and not email:
            raise ValueError("Either a user id or email must be provided.")

        query = User.objects.filter(is_active=True)
        if exclude_users_scheduled_to_be_deleted:
            query = query.filter(profile__to_be_deleted=False)

        if user_id:
            query = query.filter(id=user_id)

        if email:
            email = normalize_email_address(email)
            query = query.filter(username=email)

        try:
            return query.get()
        except User.DoesNotExist:
            raise UserNotFound("The user with the provided parameters is not found.")

    def create_user(
        self,
        name: str,
        email: str,
        password: str,
        language: Optional[str] = None,
        group_invitation_token: Optional[str] = None,
        template: Template = None,
        auth_provider: Optional[AuthProviderModel] = None,
    ) -> AbstractUser:
        """
        Creates a new user with the provided information and creates a new group and
        application for him. If the optional group invitation is provided then the user
        joins that group without creating a new one.

        :param name: The name of the new user.
        :param email: The e-mail address of the user, this is also the username.
        :param password: The password of the user.
        :param language: The language selected by the user.
        :param group_invitation_token: If provided and valid, the invitation will be
            accepted and initial group will not be created.
        :param template: If provided, that template will be installed into the newly
            created group.
        :param authentication_provider: If provided, a reference to the authentication
            provider will be stored in order to be able to provide different options
            for the user to login.
        :raises: UserAlreadyExist: When a user with the provided username (email)
            already exists.
        :raises GroupInvitationEmailMismatch: If the group invitation email does not
            match the one of the user.
        :raises SignupDisabledError: If signing up is disabled.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The user object.
        """

        core_handler = CoreHandler()

        email = normalize_email_address(email)
        user_query = User.objects.filter(Q(email=email) | Q(username=email))
        if user_query.exists():
            user = user_query.first()
            if user.is_active:
                raise UserAlreadyExist(f"A user with email {email} already exists.")
            else:
                raise DeactivatedUserException(
                    f"User with email {email} has been deactivated."
                )

        group_invitation = None
        group_user = None

        if group_invitation_token:
            group_invitation = core_handler.get_group_invitation_by_token(
                group_invitation_token
            )

            if email != group_invitation.email:
                raise GroupInvitationEmailMismatch(
                    "The email address of the invitation does not match the one of the "
                    "user."
                )

        instance_settings = core_handler.get_settings()
        allow_new_signups = instance_settings.allow_new_signups
        allow_signup_for_invited_user = (
            instance_settings.allow_signups_via_group_invitations
            and group_invitation is not None
        )
        if not (allow_new_signups or allow_signup_for_invited_user):
            raise DisabledSignupError("Sign up is disabled.")

        user = User(first_name=name, email=email, username=email)

        if password is not None:
            try:
                validate_password(password, user)
            except ValidationError as e:
                raise PasswordDoesNotMatchValidation(e.messages)
            user.set_password(password)

        if not User.objects.exists():
            # This is the first ever user created in this baserow instance and
            # therefore the administrator user, lets give them staff rights so they
            # can set baserow wide settings.
            user.is_staff = True

        if instance_settings.show_admin_signup_page:
            instance_settings.show_admin_signup_page = False
            instance_settings.save()

        user.save()

        # Immediately create the one-to-one relationship with the user profile
        # so we can safely use it everywhere else in the code.
        language = language or settings.LANGUAGE_CODE
        UserProfile.objects.create(user=user, language=language)

        if group_invitation_token:
            group_user = core_handler.accept_group_invitation(user, group_invitation)

        if not group_user:
            with translation.override(language):
                group_user = core_handler.create_group(
                    user=user, name=_("%(name)s's group") % {"name": name}
                )

        if not group_invitation_token and template:
            core_handler.install_template(user, group_user.group, template)

        # Call the user_created method for each plugin that is in the registry.
        for plugin in plugin_registry.registry.values():
            plugin.user_created(user, group_user.group, group_invitation, template)

        # register the authentication provider used to create the user
        if auth_provider is None:
            auth_provider = PasswordProviderHandler.get()
        auth_provider.user_signed_in(user)

        return user

    def update_user(
        self,
        user: AbstractUser,
        first_name: Optional[str] = None,
        language: Optional[str] = None,
    ) -> AbstractUser:
        """
        Updates the user's account editable properties. Handles the scenario
        when a user edits his own account.

        :param user: The user instance to update.
        :param first_name: The new user first name.
        :param language: The language selected by the user.
        :return: The user object.
        """

        if first_name is not None:
            user.first_name = first_name
            user.save()

        if language is not None:
            user.profile.language = language
            user.profile.save()

        user_updated.send(self, performed_by=user, user=user)

        return user

    def get_reset_password_signer(self) -> URLSafeTimedSerializer:
        """
        Instantiates the password reset serializer that can dump and load values.

        :return: The itsdangerous serializer.
        :rtype: URLSafeTimedSerializer
        """

        return URLSafeTimedSerializer(settings.SECRET_KEY, "user-reset-password")

    def send_reset_password_email(self, user: AbstractUser, base_url: str):
        """
        Sends an email containing a password reset url to the user.

        :param user: The user instance.
        :param base_url: The base url of the frontend, where the user can reset his
            password. The reset token is appended to the URL (base_url + '/TOKEN').
            Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :raises: ResetPasswordDisabledError: If the reset password is disabled.
        """

        if not CoreHandler().get_settings().allow_reset_password:
            raise ResetPasswordDisabledError("Reset password is disabled")

        parsed_base_url = urlparse(base_url)
        if parsed_base_url.hostname != settings.PUBLIC_WEB_FRONTEND_HOSTNAME:
            raise BaseURLHostnameNotAllowed(
                f"The hostname {parsed_base_url.netloc} is not allowed."
            )

        signer = self.get_reset_password_signer()
        signed_user_id = signer.dumps(user.id)

        if not base_url.endswith("/"):
            base_url += "/"

        reset_url = urljoin(base_url, signed_user_id)

        with translation.override(user.profile.language):
            email = ResetPasswordEmail(user, reset_url, to=[user.email])
            email.send()

    def reset_password(self, token: str, password: str) -> AbstractUser:
        """
        Changes the password of a user if the provided token is valid.

        :param token: The signed token that was send to the user.
        :param password: The new password of the user.
        :raises SignatureExpired: When the provided token's signature has expired.
        :raises UserNotFound: When a user related to the provided token has not been
            found.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The updated user instance.
        """

        if not CoreHandler().get_settings().allow_reset_password:
            raise ResetPasswordDisabledError("Reset password is disabled.")

        signer = self.get_reset_password_signer()
        user_id = signer.loads(token, max_age=settings.RESET_PASSWORD_TOKEN_MAX_AGE)

        user = self.get_active_user(user_id=user_id)

        try:
            validate_password(password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(password)
        user.save()

        return user

    def change_password(
        self, user: AbstractUser, old_password: str, new_password: str
    ) -> AbstractUser:
        """
        Changes the password of the provided user if the old password matches the
        existing one.

        :param user: The user for which the password needs to be changed.
        :param old_password: The old password of the user. This must match with the
            existing password else the InvalidPassword exception is raised.
        :param new_password: The new password of the user. After changing the user
            can only authenticate with this password.
        :raises InvalidPassword: When the provided old password is incorrect.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The changed user instance.
        """

        if not user.check_password(old_password):
            raise InvalidPassword("The provided old password is incorrect.")

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(new_password)
        user.save()

        return user

    def user_signed_in_via_provider(
        self, user: AbstractUser, authentication_provider: AuthProviderModel
    ):
        """
        Registers the authentication provider used to authenticate the user.

        :param user: The user instance.
        :param authentication_provider: The authentication provider instance.
        """

        authentication_provider.user_signed_in(user)
        self.user_signed_in(user)

    def user_signed_in(self, user: AbstractUser):
        """
        Executes tasks and informs plugins when a user signs in.

        :param user: The user that has just signed in.
        """

        if user.profile.to_be_deleted:
            self.cancel_user_deletion(user)

        update_last_login(None, user)
        UserLogEntry.objects.create(actor=user, action="SIGNED_IN")

        # Call the user_signed_in method for each plugin that is in the registry to
        # notify all plugins that a user has signed in.
        from baserow.core.registries import plugin_registry

        for plugin in plugin_registry.registry.values():
            plugin.user_signed_in(user)

    def user_refreshed_session_token(self, user: AbstractUser):
        """
        Adds a UserLogEntry for statistics.

        :param user: The user that has just refreshed his session.
        """

        action = "REFRESHED_TOKEN"
        now = timezone.now()
        refreshed_token_entry = (
            UserLogEntry.objects.filter(actor=user, action=action)
            .extra(
                {"date": "date_trunc('hour', timestamp at time zone %s)"},
                select_params=(str(now.tzinfo),),
            )
            .first()
        )
        if refreshed_token_entry is None:
            UserLogEntry.objects.create(actor=user, action=action)
        else:
            refreshed_token_entry.timestamp = now
            refreshed_token_entry.save()

    def schedule_user_deletion(self, user: AbstractUser):
        """
        Schedules the user account deletion. The user is flagged as `to_be_deleted` and
        will be deleted after a predefined grace delay unless the user
        cancel his account deletion by log in again.
        This action sends an email to the user to explain the process.

        :param user: The user to flag as `to_be_deleted`.
        :raises UserIsLastAdmin: When the user cannot be deleted as he is the last
            admin.
        """

        if (
            user.is_staff
            and not User.objects.filter(is_staff=True).exclude(pk=user.pk).exists()
        ):
            raise UserIsLastAdmin("You are the last admin of the instance.")

        before_user_deleted.send(self, user=user)

        user.profile.to_be_deleted = True
        user.profile.save()

        # update last login to be more accurate
        update_last_login(None, user)

        core_settings = CoreHandler().get_settings()

        days_left = getattr(
            settings,
            "FORCE_ACCOUNT_DELETION_GRACE_DELAY",
            timedelta(days=core_settings.account_deletion_grace_delay),
        ).days

        with translation.override(user.profile.language):
            email = AccountDeletionScheduled(user, days_left, to=[user.email])
            email.send()

        user_deleted.send(self, performed_by=user, user=user)

    def cancel_user_deletion(self, user: AbstractUser):
        """
        Cancels a previously scheduled user account deletion. This action send an email
        to the user to confirm the cancelation.

        :param user: The user currently in pending deletion.
        """

        user.profile.to_be_deleted = False
        user.profile.save()

        with translation.override(user.profile.language):
            email = AccountDeletionCanceled(user, to=[user.email])
            email.send()

        user_restored.send(self, performed_by=user, user=user)

    def delete_expired_users(self, grace_delay: Optional[timedelta] = None):
        """
        Executes all previously scheduled user account deletions for which
        the `last_login` date is earlier than the defined grace delay. If the users
        are the last admin of some groups, these groups are also deleted. An email
        is sent to confirm the user account deletion. This task is periodically
        executed.

        :param grace_delay: A timedelta that indicate the delay before permanently
          delete a user account. If this parameter is not given, the delay is defined
          in the core Baserow settings.
        """

        if not grace_delay:
            core_settings = CoreHandler().get_settings()
            grace_delay = getattr(
                settings,
                "FORCE_ACCOUNT_DELETION_GRACE_DELAY",
                timedelta(days=core_settings.account_deletion_grace_delay),
            )

        limit_date = timezone.now() - grace_delay

        users_to_delete = User.objects.filter(
            profile__to_be_deleted=True, last_login__lt=limit_date
        )

        group_users = GroupUser.objects.filter(user__in=users_to_delete)

        deleted_user_info = []
        for u in users_to_delete.all():
            group_ids = [gu.group_id for gu in group_users if gu.user_id == u.id]
            deleted_user_info.append(
                (u.id, u.username, u.email, u.profile.language, group_ids)
            )

        # A group need to be deleted if there was an admin before and there is no
        # *active* admin after the users deletion.
        groups_to_be_deleted = Group.objects.annotate(
            admin_count_after=Count(
                "groupuser",
                filter=(
                    Q(groupuser__permissions="ADMIN")
                    & ~Q(
                        groupuser__user__in=User.objects.filter(
                            (
                                Q(profile__to_be_deleted=True)
                                & Q(last_login__lt=limit_date)
                            )
                            | Q(is_active=False)
                        )
                    )
                ),
            ),
        ).filter(template=None, admin_count_after=0)

        with transaction.atomic():
            for group in groups_to_be_deleted:
                # Here we use the trash handler to be sure that we delete every thing
                # related the groups like
                TrashHandler.permanently_delete(group)
            users_to_delete.delete()

        for (id, username, email, language, group_ids) in deleted_user_info:
            with translation.override(language):
                email = AccountDeleted(username, to=[email])
                email.send()
            user_permanently_deleted.send(self, user_id=id, group_ids=group_ids)
