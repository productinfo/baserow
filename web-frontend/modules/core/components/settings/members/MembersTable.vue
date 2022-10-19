<template>
  <div>
    <CrudTable
      ref="crudTable"
      :service="service"
      :columns="columns"
      row-id-key="id"
      @row-context="onRowContext"
    >
      <template #header-left-side>
        <div class="crudtable__header-title">
          {{
            $t('membersSettings.membersTable.title', {
              userAmount: group.users.length || 0,
              groupName: group.name,
            })
          }}
        </div>
      </template>
      <template #header-right-side>
        <div
          class="button margin-left-2 button--large"
          @click="$refs.inviteModal.show()"
        >
          {{ $t('membersSettings.membersTable.inviteMember') }}
        </div>
      </template>
      <template #menus>
        <EditMemberContext
          ref="editMemberContext"
          :group="group"
          :member="editMember"
          @refresh="refresh"
        ></EditMemberContext>
      </template>
    </CrudTable>
    <GroupMemberInviteModal
      ref="inviteModal"
      :group="group"
      @invite-submitted="
        $router.push({
          name: 'settings-invites',
          params: {
            groupId: group.id,
          },
        })
      "
    />
  </div>
</template>

<script>
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import GroupService from '@baserow/modules/core/services/group'
import { mapGetters } from 'vuex'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import DropdownField from '@baserow/modules/core/components/crudTable/fields/DropdownField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import { notifyIf } from '@baserow/modules/core/utils/error'
import GroupMemberInviteModal from '@baserow/modules/core/components/group/GroupMemberInviteModal'
import EditMemberContext from '@baserow/modules/core/components/settings/members/EditMemberContext'

export default {
  name: 'MembersTable',
  components: { EditMemberContext, CrudTable, GroupMemberInviteModal },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      editMember: {},
    }
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
    service() {
      const service = GroupService(this.$client)
      const options = {
        ...service.options,
        urlParams: { groupId: this.group.id },
      }
      return {
        ...service,
        options,
      }
    },
    columns() {
      return [
        new CrudTableColumn(
          'name',
          this.$t('membersSettings.membersTable.columns.name'),
          SimpleField,
          true,
          true
        ),
        new CrudTableColumn(
          'email',
          this.$t('membersSettings.membersTable.columns.email'),
          SimpleField,
          true
        ),
        new CrudTableColumn(
          'permissions',
          this.$t('membersSettings.membersTable.columns.role'),
          DropdownField,
          false,
          false,
          false,
          {
            options: [
              {
                value: 'ADMIN',
                name: this.$t('permission.admin'),
                description: this.$t('permission.adminDescription'),
              },
              {
                value: 'MEMBER',
                name: this.$t('permission.member'),
                description: this.$t('permission.memberDescription'),
              },
            ],
            disabled: (row) => row.user_id === this.userId,
            inputCallback: this.roleUpdate,
            action: {
              label: this.$t('membersSettings.membersTable.actions.remove'),
              colorClass: 'color--deep-dark-red',
              onClickEventName: 'remove',
            },
          }
        ),
        new CrudTableColumn(null, null, MoreField, false, false, true),
      ]
    },
  },
  methods: {
    onRowContext({ row, event, target }) {
      if (target === undefined) {
        target = {
          left: event.clientX,
          top: event.clientY,
        }
      }

      const action = row.id === this.editMember.id ? 'toggle' : 'show'
      this.editMember = row
      this.$refs.editMemberContext[action](target, 'bottom', 'left', 4)
    },
    async refresh() {
      await this.$refs.crudTable.fetch()
    },
    async roleUpdate(permissionsNew, { permissions, id }) {
      if (permissions === permissionsNew) {
        return
      }

      try {
        await GroupService(this.$client).updateUser(id, {
          permissions: permissionsNew,
        })
        await this.$store.dispatch('group/forceUpdateGroupUser', {
          groupId: this.group.id,
          id,
          values: { permissions: permissionsNew },
        })
      } catch (error) {
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
