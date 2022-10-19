<template>
  <div>
    <CrudTable
      ref="crudTable"
      :service="service"
      :columns="columns"
      row-id-key="id"
      @rows-update="invitesAmount = $event.length"
      @row-context="onRowContext"
    >
      <template #header-left-side>
        <div class="crudtable__header-title">
          {{
            $t('membersSettings.invitesTable.title', {
              invitesAmount,
              groupName: group.name,
            })
          }}
        </div>
      </template>
      <template #header-right-side>
        <div
          class="button button--large margin-left-2"
          @click="$refs.inviteModal.show()"
        >
          {{ $t('membersSettings.membersTable.inviteMember') }}
        </div>
      </template>
      <template #menus>
        <EditInviteContext
          ref="editInviteContext"
          :invitation="editInvitation"
          @refresh="$refs.crudTable.fetch()"
        ></EditInviteContext>
      </template>
    </CrudTable>
    <GroupMemberInviteModal
      ref="inviteModal"
      :group="group"
      @invite-submitted="$refs.crudTable.fetch()"
    />
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import GroupService from '@baserow/modules/core/services/group'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import DropdownField from '@baserow/modules/core/components/crudTable/fields/DropdownField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import GroupMemberInviteModal from '@baserow/modules/core/components/group/GroupMemberInviteModal'
import EditInviteContext from '@baserow/modules/core/components/settings/members/EditInviteContext'

export default {
  name: 'MembersInvitesTable',
  components: { EditInviteContext, CrudTable, GroupMemberInviteModal },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      editInvitation: {},
      invitesAmount: 0,
    }
  },
  computed: {
    service() {
      const service = GroupService(this.$client)

      service.options.baseUrl = ({ groupId }) =>
        `/groups/invitations/group/${groupId}/`

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
          'email',
          this.$t('membersSettings.invitesTable.columns.email'),
          SimpleField,
          true,
          true
        ),
        new CrudTableColumn(
          'message',
          this.$t('membersSettings.invitesTable.columns.message'),
          SimpleField,
          true
        ),
        new CrudTableColumn(
          'permissions',
          this.$t('membersSettings.invitesTable.columns.role'),
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
            inputCallback: this.roleUpdate,
            action: {
              label: this.$t('membersSettings.invitesTable.actions.remove'),
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

      const action = row.id === this.editInvitation.id ? 'toggle' : 'show'
      this.editInvitation = row
      this.$refs.editInviteContext[action](target, 'bottom', 'left', 4)
    },
    async roleUpdate(permissionsNew, { permissions, id }) {
      if (permissionsNew === permissions) {
        return
      }

      try {
        await GroupService(this.$client).updateInvitation(id, {
          permissions: permissionsNew,
        })
      } catch (error) {
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
