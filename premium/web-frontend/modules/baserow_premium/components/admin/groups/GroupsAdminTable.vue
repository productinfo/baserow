<template>
  <CrudTable
    :columns="columns"
    :service="service"
    row-id-key="id"
    @edit-group="displayEditGroupContext"
    @show-hidden-groups="displayHiddenUsers"
    @row-context="onRowContext"
  >
    <template #header-left-side>
      <div class="crudtable__header-title">
        {{ $t('groupsAdminTable.allGroups') }}
      </div>
    </template>
    <template #menus="slotProps">
      <EditGroupContext
        ref="editGroupContext"
        :group="editGroup"
        @group-deleted="slotProps.deleteRow"
      >
      </EditGroupContext>
      <HiddenUsersContext
        ref="hiddenUsersContext"
        :hidden-values="hiddenUsers"
      ></HiddenUsersContext>
    </template>
  </CrudTable>
</template>

<script>
import GroupsAdminService from '@baserow_premium/services/admin/groups'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import GroupUsersField from '@baserow_premium/components/admin/groups/fields/GroupUsersField'
import GroupNameField from '@baserow_premium/components/admin/groups/fields/GroupNameField'
import GroupMoreField from '@baserow_premium/components/admin/groups/fields/GroupMoreField'
import EditGroupContext from '@baserow_premium/components/admin/groups/contexts/EditGroupContext'
import HiddenUsersContext from '@baserow_premium/components/admin/groups/contexts/HiddenUsersContext'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'

export default {
  name: 'GroupsAdminTable',
  components: {
    CrudTable,
    HiddenUsersContext,
    EditGroupContext,
  },
  data() {
    this.columns = [
      new CrudTableColumn(
        'name',
        () => this.$t('groupsAdminTable.name'),
        GroupNameField,
        true,
        true
      ),
      new CrudTableColumn(
        'users',
        () => this.$t('groupsAdminTable.members'),
        GroupUsersField
      ),
      new CrudTableColumn(
        'application_count',
        () => this.$t('groupsAdminTable.applications'),
        SimpleField,
        true
      ),
      new CrudTableColumn(
        'created_on',
        () => this.$t('groupsAdminTable.created'),
        LocalDateField,
        true
      ),
      new CrudTableColumn('more', '', GroupMoreField, false, false, true),
    ]
    this.service = GroupsAdminService(this.$client)
    return {
      editGroup: {},
      hiddenUsers: [],
    }
  },
  methods: {
    displayEditGroupContext(event) {
      const action = event.group.id === this.editGroup.id ? 'toggle' : 'show'
      this.editGroup = event.group
      this.$refs.editGroupContext[action](event.target, 'bottom', 'left', 4)
    },
    onRowContext({ row, event }) {
      this.displayEditGroupContext({
        group: row,
        target: {
          left: event.clientX,
          top: event.clientY,
        },
      })
    },
    displayHiddenUsers(event) {
      const action = this.hiddenUsers === event.hiddenValues ? 'toggle' : 'show'
      this.hiddenUsers = event.hiddenValues
      this.$refs.hiddenUsersContext[action](event.target, 'bottom', 'left', 4)
    },
  },
}
</script>
