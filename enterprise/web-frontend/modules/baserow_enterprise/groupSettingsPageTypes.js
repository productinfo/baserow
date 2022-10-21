import { GroupSettingsPageType } from '@baserow/modules/core/groupSettingsPageTypes'

export class TeamsGroupSettingsPageType extends GroupSettingsPageType {
  getType() {
    return 'teams'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('membersSettings.teamsTabTitle')
  }

  getRoute(group) {
    return {
      name: 'settings-teams',
      params: {
        groupId: group.id,
      },
    }
  }
}
