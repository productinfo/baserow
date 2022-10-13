import { AdminType } from '@baserow/modules/core/adminTypes'
import { PremiumPlugin } from '@baserow_premium/plugins'

class EnterpriseAdminType extends AdminType {
  getDeactivatedText() {
    return this.app.i18n.t('enterprise.deactivated')
  }

  isDeactivated() {
    // TODO: change with enterprise license
    return !this.app.$registry
      .get('plugin', PremiumPlugin.getType())
      .activeLicenseHasPremiumFeatures()
  }
}

export class AuthProvidersType extends EnterpriseAdminType {
  static getType() {
    return 'auth-providers'
  }

  getIconClass() {
    return 'sign-in-alt'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('enterprise.adminType.Authentication')
  }

  getRouteName() {
    return 'admin-auth-providers'
  }

  getOrder() {
    return 100
  }
}
