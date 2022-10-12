import { AuthProviderType } from '@baserow/modules/core/authProviderTypes'

import SamlLoginAction from '@baserow_enterprise/components/admin/login/SamlLoginAction'
import ProviderItem from '@baserow_enterprise/components/admin/AuthProviderItem'
import SamlSettingsForm from '@baserow_enterprise/components/admin/forms/SamlSettingsForm'
import OAuth2SettingsForm from '@baserow_enterprise/components/sso/forms/OAuth2SettingsForm.vue'
import GitLabSettingsForm from '@baserow_enterprise/components/sso/forms/GitLabSettingsForm.vue'
import OpenIdConnectSettingsForm from '@baserow_enterprise/components/sso/forms/OpenIdConnectSettingsForm.vue'
import OAuth2LoginButton from '@baserow_enterprise/components/sso/oauth2/loginButton'


export class SamlAuthProviderType extends AuthProviderType {
  getType() {
    return 'saml'
  }

  getIconClass() {
    return 'fas fa-key'
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

  getName() {
    return 'Google'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : `Google`
  }

  getLoginButtonComponent() {
    return OAuth2LoginButton
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

  getName() {
    return 'Facebook'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : `Facebook`
  }

  getLoginButtonComponent() {
    return OAuth2LoginButton
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

  getName() {
    return 'GitHub'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : `GitHub`
  }

  getLoginButtonComponent() {
    return OAuth2LoginButton
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

  getName() {
    return 'GitLab'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : `GitLab`
  }

  getLoginButtonComponent() {
    return OAuth2LoginButton
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

  getName() {
    return 'OpenId Connect'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : `OpenId Connect`
  }

  getLoginButtonComponent() {
    return OAuth2LoginButton
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
