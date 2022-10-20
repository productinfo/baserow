<template>
  <Modal>
    <Tabs>
      <Tab :title="$t('RoleAssignmentModal.membersTab')">
        <SelectMembersList
          class="margin-top-2"
          :users="users"
          show-role-selector
        />
      </Tab>
      <Tab :title="$t('RoleAssignmentModal.teamsTab')">
        <SelectTeamsList
          class="margin-top-2"
          :users="teams"
          show-role-selector
        />
      </Tab>
    </Tabs>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/mixins/modal'
import SelectMembersList from '@baserow_enterprise/components/rbac/SelectMembersList'
import SelectTeamsList from '@baserow_enterprise/components/rbac/SelectTeamsList'

export default {
  name: 'RoleAssignmentModal',
  components: { SelectTeamsList, SelectMembersList },
  mixins: [Modal],
  props: {
    users: {
      type: Array,
      required: false,
      default: () => [
        { id: 0, name: 'alex', email: 'test@test.com' },
        { id: 1, name: 'john', email: 'test2@test.com' },
        { id: 2, name: 'john', email: 'test2@test.com' },
        { id: 3, name: 'john', email: 'test2@test.com' },
        { id: 4, name: 'john', email: 'test2@test.com' },
        { id: 5, name: 'john', email: 'test2@test.com' },
        { id: 6, name: 'john', email: 'test2@test.com' },
        { id: 7, name: 'john', email: 'test2@test.com' },
        { id: 8, name: 'john', email: 'test2@test.com' },
        { id: 9, name: 'john', email: 'test2@test.com' },
        { id: 10, name: 'john', email: 'test2@test.com' },
        { id: 11, name: 'john', email: 'test2@test.com' },
        { id: 12, name: 'john', email: 'test2@test.com' },
      ],
    },
    teams: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
}
</script>
