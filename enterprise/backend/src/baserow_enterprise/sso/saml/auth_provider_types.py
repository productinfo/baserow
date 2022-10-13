from typing import Any, Dict, List, Optional

from baserow_enterprise.api.sso.saml.errors import (
    ERROR_SAML_PROVIDER_WITH_SAME_DOMAIN_ALREADY_EXISTS,
)
from baserow_enterprise.api.sso.saml.exceptions import (
    SamlProviderWithSameDomainAlreadyExists,
)
from baserow_enterprise.api.sso.saml.validators import (
    validate_saml_metadata,
    validate_unique_saml_domain,
)
from baserow_enterprise.license.handler import (
    check_active_enterprise_license,
    has_active_enterprise_license,
)
from rest_framework import serializers

from baserow.api.utils import ExceptionMappingType
from baserow.core.auth_provider.auth_provider_types import AuthProviderType
from baserow.core.auth_provider.validators import validate_domain

from .models import SamlAuthProviderModel


class SamlAuthProviderType(AuthProviderType):
    """
    The SAML authentication provider type allows users to login using SAML.
    """

    type = "saml"
    model_class = SamlAuthProviderModel
    allowed_fields: List[str] = [
        "id",
        "domain",
        "type",
        "enabled",
        "metadata",
        "is_verified",
    ]
    serializer_field_names = ["domain", "metadata", "enabled", "is_verified"]
    serializer_field_overrides = {
        "domain": serializers.CharField(validators=[validate_domain], required=True),
        "metadata": serializers.CharField(
            validators=[validate_saml_metadata], required=True
        ),
        "is_verified": serializers.BooleanField(required=False, read_only=True),
    }
    api_exceptions_map: ExceptionMappingType = {
        SamlProviderWithSameDomainAlreadyExists: ERROR_SAML_PROVIDER_WITH_SAME_DOMAIN_ALREADY_EXISTS
    }

    def before_create(self, user, **values):
        check_active_enterprise_license(user)
        validate_unique_saml_domain(values["domain"])
        return super().before_create(user, **values)

    def before_update(self, user, provider, **values):
        check_active_enterprise_license(user)
        if "domain" in values:
            validate_unique_saml_domain(values["domain"], provider)
        return super().before_update(user, provider, **values)

    def get_login_options(self, **kwargs) -> Optional[Dict[str, Any]]:

        enterprise_license_active = has_active_enterprise_license()
        configured_domains = SamlAuthProviderModel.objects.filter(enabled=True).count()
        if not enterprise_license_active or not configured_domains:
            return None

        return {
            "type": self.type,
            # if configure_domains = 1, we can redirect directly the user to the
            # IdP login page without asking for the email
            "domain_required": configured_domains > 1,
        }

    def can_create_new_providers(self):
        return True
