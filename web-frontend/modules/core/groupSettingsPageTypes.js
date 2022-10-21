import { Registerable } from '@baserow/modules/core/registry'

export class GroupSettingsPageType extends Registerable {
  /**
   * The name of the page in the tabs navigation at the top of the page.
   */
  getName() {
    return null
  }

  constructor(...args) {
    super(...args)
    this.type = this.getType()

    if (this.type === null) {
      throw new Error('The type name of a group settings page must be set.')
    }
  }

  serialize() {
    return {
      type: this.type,
      name: this.getName(),
    }
  }

  getRoute() {
    throw new Error('The `getRoute` method must be set.')
  }
}

export class MembersGroupSettingsPageType extends GroupSettingsPageType {
  getType() {
    return 'members'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('membersSettings.membersTabTitle')
  }

  getRoute(group) {
    return {
      name: 'settings-members',
      params: {
        groupId: group.id,
      },
    }
  }
}

export class InvitesGroupSettingsPageType extends GroupSettingsPageType {
  getType() {
    return 'invites'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('membersSettings.invitesTabTitle')
  }

  getRoute(group) {
    return {
      name: 'settings-invites',
      params: {
        groupId: group.id,
      },
    }
  }
}
