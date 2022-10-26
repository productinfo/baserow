import { AuthProviderType } from '@baserow/modules/core/authProviderTypes'

import SamlLoginAction from '@baserow_enterprise/components/admin/login/SamlLoginAction'
import ProviderItem from '@baserow_enterprise/components/admin/AuthProviderItem'
import SamlSettingsForm from '@baserow_enterprise/components/admin/forms/SamlSettingsForm'
import OAuth2SettingsForm from '@baserow_enterprise/components/admin/forms/OAuth2SettingsForm.vue'
import GitLabSettingsForm from '@baserow_enterprise/components/admin/forms/GitLabSettingsForm.vue'
import OpenIdConnectSettingsForm from '@baserow_enterprise/components/admin/forms/OpenIdConnectSettingsForm.vue'
import LoginButton from '@baserow_enterprise/components/admin/login/LoginButton.vue'

import SAMLIcon from '@baserow_enterprise/assets/images/providers/LockKey.svg'
import GoogleIcon from '@baserow_enterprise/assets/images/providers/Google.svg'
import FacebookIcon from '@baserow_enterprise/assets/images/providers/Facebook.svg'
import GitHubIcon from '@baserow_enterprise/assets/images/providers/GitHub.svg'
import GitLabIcon from '@baserow_enterprise/assets/images/providers/GitLab.svg'
import OpenIdIcon from '@baserow_enterprise/assets/images/providers/OpenID.svg'

export class SamlAuthProviderType extends AuthProviderType {
  getType() {
    return 'saml'
  }

  getIconClass() {
    return 'fas fa-key'
  }

  getIcon() {
    return SAMLIcon
  }

  getName() {
    return 'SAML SSO provider'
  }

  getProviderName(provider) {
    return `SAML: ${provider.domain}`
  }

  getLoginActionComponent() {
    return SamlLoginAction
  }

  getAdminListComponent() {
    return ProviderItem
  }

  getAdminSettingsFormComponent() {
    return SamlSettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      redirectUrl: authProviderOption.redirect_url,
      domainRequired: authProviderOption.domain_required,
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      isVerified: authProviderType.is_verified,
      metadata: authProviderType.metadata,
      ...populated,
    }
  }
}

export class GoogleAuthProviderType extends AuthProviderType {
  getType() {
    return 'google'
  }

  getIconClass() {
    return 'fas fa-key'
  }

  getIcon() {
    return GoogleIcon
  }

  getName() {
    return 'Google'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : `Google`
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return ProviderItem
  }

  getAdminSettingsFormComponent() {
    return OAuth2SettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class FacebookAuthProviderType extends AuthProviderType {
  getType() {
    return 'facebook'
  }

  getIconClass() {
    return 'fas fa-key'
  }

  getIcon() {
    return FacebookIcon
  }

  getName() {
    return 'Facebook'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return ProviderItem
  }

  getAdminSettingsFormComponent() {
    return OAuth2SettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class GitHubAuthProviderType extends AuthProviderType {
  getType() {
    return 'github'
  }

  getIconClass() {
    return 'fas fa-key'
  }

  getIcon() {
    return GitHubIcon
  }

  getName() {
    return 'GitHub'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return ProviderItem
  }

  getAdminSettingsFormComponent() {
    return OAuth2SettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class GitLabAuthProviderType extends AuthProviderType {
  getType() {
    return 'gitlab'
  }

  getIconClass() {
    return 'fas fa-key'
  }

  getIcon() {
    return GitLabIcon
  }

  getName() {
    return 'GitLab'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return ProviderItem
  }

  getAdminSettingsFormComponent() {
    return GitLabSettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class OpenIdConnectAuthProviderType extends AuthProviderType {
  getType() {
    return 'openid_connect'
  }

  getIconClass() {
    return 'fas fa-key'
  }

  getIcon() {
    return OpenIdIcon
  }

  getName() {
    return 'OpenID Connect'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return ProviderItem
  }

  getAdminSettingsFormComponent() {
    return OpenIdConnectSettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}
