<template>
  <CrudTable
    :columns="columns"
    :service="service"
    row-id-key="id"
    @edit-user="displayEditUserContext"
    @show-hidden-groups="displayHiddenGroups"
    @row-context="onRowContext"
  >
    <template #header-left-side>
      <div class="crudtable__header-title">
        {{ $t('usersAdminTable.allUsers') }}
      </div>
    </template>
    <template #menus="slotProps">
      <EditUserContext
        ref="editUserContext"
        :user="editUser"
        @delete-user="slotProps.deleteRow"
        @update="slotProps.updateRow"
      >
      </EditUserContext>
      <HiddenGroupsContext
        ref="hiddenGroupsContext"
        :hidden-values="hiddenGroups"
      ></HiddenGroupsContext>
    </template>
  </CrudTable>
</template>

<script>
import UserAdminService from '@baserow_premium/services/admin/users'
import UsernameField from '@baserow_premium/components/admin/users/fields/UsernameField'
import MoreField from '@baserow_premium/components/admin/users/fields/MoreField'
import UserGroupsField from '@baserow_premium/components/admin/users/fields/UserGroupsField'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import ActiveField from '@baserow_premium/components/admin/users/fields/ActiveField'
import EditUserContext from '@baserow_premium/components/admin/users/contexts/EditUserContext'
import HiddenGroupsContext from '@baserow_premium/components/admin/users/contexts/HiddenGroupsContext'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'

export default {
  name: 'UsersAdminTable',
  components: {
    HiddenGroupsContext,
    CrudTable,
    EditUserContext,
  },
  data() {
    this.columns = [
      new CrudTableColumn(
        'username',
        () => this.$t('usersAdminTable.username'),
        UsernameField,
        true,
        true
      ),
      new CrudTableColumn(
        'name',
        () => this.$t('usersAdminTable.name'),
        SimpleField,
        true
      ),
      new CrudTableColumn(
        'groups',
        () => this.$t('usersAdminTable.groups'),
        UserGroupsField
      ),
      new CrudTableColumn(
        'last_login',
        () => this.$t('usersAdminTable.lastLogin'),
        LocalDateField,
        true
      ),
      new CrudTableColumn(
        'date_joined',
        () => this.$t('usersAdminTable.dateJoined'),
        LocalDateField,
        true
      ),
      new CrudTableColumn(
        'is_active',
        () => this.$t('premium.user.active'),
        ActiveField,
        true
      ),
      new CrudTableColumn('more', '', MoreField, false, false, true),
    ]
    this.service = UserAdminService(this.$client)
    return {
      editUser: {},
      hiddenGroups: [],
    }
  },
  methods: {
    displayEditUserContext(event) {
      const action = event.user.id === this.editUser.id ? 'toggle' : 'show'
      this.editUser = event.user
      this.$refs.editUserContext[action](event.target, 'bottom', 'left', 4)
    },
    onRowContext({ row, event }) {
      this.displayEditUserContext({
        user: row,
        target: {
          left: event.clientX,
          top: event.clientY,
        },
      })
    },
    displayHiddenGroups(event) {
      const action =
        this.hiddenGroups === event.hiddenValues ? 'toggle' : 'show'
      this.hiddenGroups = event.hiddenValues
      this.$refs.hiddenGroupsContext[action](event.target, 'bottom', 'left', 4)
    },
  },
}
</script>
