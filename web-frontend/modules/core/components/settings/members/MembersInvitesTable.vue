<template>
  <div>
    <CrudTable
      ref="crudTable"
      :service="service"
      :columns="columns"
      row-id-key="id"
      @rows-update="invitesAmount = $event.length"
      @remove="remove"
      @copy-email="copyEmail"
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
    </CrudTable>
    <MembersInviteModal
      ref="inviteModal"
      :group="group"
      @invite-submitted="$refs.crudTable.fetch()"
    />
  </div>
</template>

<script>
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import { mapGetters } from 'vuex'
import GroupService from '@baserow/modules/core/services/group'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import DropdownField from '@baserow/modules/core/components/crudTable/fields/DropdownField'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ActionsField from '@baserow/modules/core/components/crudTable/fields/ActionsField'
import MembersInviteModal from '@baserow/modules/core/components/settings/members/MembersInviteModal'

export default {
  name: 'MembersInvitesTable',
  components: { CrudTable, MembersInviteModal },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      invitesAmount: 0,
    }
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
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
          true,
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
        new CrudTableColumn(null, null, ActionsField, false, false, true, {
          actions: [
            {
              label: this.$t('membersSettings.invitesTable.actions.copyEmail'),
              onClickEventName: 'copy-email',
            },
            {
              label: this.$t('membersSettings.invitesTable.actions.remove'),
              onClickEventName: 'remove',
              disabled: (row) => row.user_id === this.userId,
              colorClass: 'color--deep-dark-red',
            },
          ],
        }),
      ]
    },
  },
  methods: {
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
    async copyEmail({ email }) {
      await navigator.clipboard.writeText(email)
      await this.$store.dispatch('notification/add', {
        type: 'success',
        title: this.$t('membersSettings.membersTable.copiedEmail.title'),
        message: this.$t('membersSettings.membersTable.copiedEmail.message'),
      })
    },
    async remove(invitation) {
      try {
        await GroupService(this.$client).deleteInvitation(invitation.id)
        await this.refresh()
      } catch (error) {
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
