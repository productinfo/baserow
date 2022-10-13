import { BaserowPlugin } from '@baserow/modules/core/plugins'
import MemberRolesContextItem from '@baserow_enterprise/components/member-roles/MemberRolesContextItem'

export class EnterprisePlugin extends BaserowPlugin {
  static getType() {
    return 'enterprise'
  }

  getAdditionalDatabaseContextComponents() {
    return [MemberRolesContextItem]
  }
}
