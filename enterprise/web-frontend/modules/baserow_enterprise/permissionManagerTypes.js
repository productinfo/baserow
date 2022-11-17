import { PermissionManagerType } from '@baserow/modules/core/permissionManagerTypes'

export class RolePermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'role'
  }

  getRolesTranslations() {
    const { i18n } = this.app

    return {
      ADMIN: {
        name: i18n.t('roles.admin.name'),
        description: i18n.t('roles.admin.description'),
      },
      BUILDER: {
        name: i18n.t('roles.builder.name'),
        description: i18n.t('roles.builder.description'),
      },
      EDITOR: {
        name: i18n.t('roles.editor.name'),
        description: i18n.t('roles.editor.description'),
      },
      COMMENTER: {
        name: i18n.t('roles.commenter.name'),
        description: i18n.t('roles.commenter.description'),
      },
      VIEWER: {
        name: i18n.t('roles.viewer.name'),
        description: i18n.t('roles.viewer.description'),
      },
      NO_ROLE: {
        name: i18n.t('roles.noRole.name'),
        description: i18n.t('roles.noRole.description'),
      },
    }
  }

  hasPermission(permissions, operation, context) {
    if (permissions[operation] === undefined) {
      return false
    }

    return (
      (permissions[operation].default &&
        !permissions[operation].exceptions.includes(context.id)) ||
      (!permissions[operation].default &&
        permissions[operation].exceptions.includes(context.id))
    )
  }
}
