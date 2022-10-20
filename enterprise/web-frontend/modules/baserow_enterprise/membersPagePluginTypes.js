// import { roles } from '@baserow_enterprise/enums/roles'
import { MembersPagePluginType } from '@baserow/modules/database/membersPagePluginTypes'

export class EnterpriseMembersPagePluginType extends MembersPagePluginType {
  static getType() {
    return 'enterprise_members_columns'
  }

  mutateMembersTableColumns(columns) {
    return this._replaceRoleColumn(columns)
  }

  mutateMembersInvitesTableColumns(columns) {
    return this._replaceRoleColumn(columns)
  }

  isDeactivated() {
    return false // TODO make this depending on if somebody has RBAC
  }

  _replaceRoleColumn(columns) {
    const existingRoleColumnIndex = columns.findIndex(
      (column) => column.key === 'permissions'
    )
    if (existingRoleColumnIndex !== -1) {
      // columns[existingRoleColumnIndex].additionalProps.roles = roles.map(({ name, uid }) => {
      //   return {
      //     value: uid,
      //     name: name,
      //     description: ''
      //   }
      // })
    }
    return columns
  }
}
