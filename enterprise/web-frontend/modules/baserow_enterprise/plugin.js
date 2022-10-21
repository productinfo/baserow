import { registerRealtimeEvents } from '@baserow_enterprise/realtime'
import { RolePermissionManagerType } from '@baserow_enterprise/permissionManagerTypes'

import { EnterpriseMembersPagePluginType } from '@baserow_enterprise/membersPagePluginTypes'
import { TeamsGroupSettingsPageType } from '@baserow_enterprise/groupSettingsPageTypes'

import en from '@baserow_enterprise/locales/en.json'
import fr from '@baserow_enterprise/locales/fr.json'
import nl from '@baserow_enterprise/locales/nl.json'
import de from '@baserow_enterprise/locales/de.json'
import es from '@baserow_enterprise/locales/es.json'
import it from '@baserow_enterprise/locales/it.json'

import teamStore from '@baserow_enterprise/store/team'

export default (context) => {
  const { store, isDev, app } = context

  // Allow locale file hot reloading
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
    i18n.mergeLocaleMessage('nl', nl)
    i18n.mergeLocaleMessage('de', de)
    i18n.mergeLocaleMessage('es', es)
    i18n.mergeLocaleMessage('it', it)
  }

  app.$registry.register(
    'permissionManager',
    new RolePermissionManagerType(context)
  )

  registerRealtimeEvents(app.$realtime)

  app.$registry.register(
    'membersPagePlugins',
    new EnterpriseMembersPagePluginType(context)
  )

  app.$registry.register(
    'groupSettingsPage',
    new TeamsGroupSettingsPageType(context)
  )

  store.registerModule('team', teamStore)
}
