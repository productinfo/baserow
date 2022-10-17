<template>
  <Modal>
    <Tabs>
      <Tab :title="$t('RoleAssignmentModal.membersTab')">
        <SubjectSelectList
          class="margin-top-2"
          :subjects="users"
          :subject-type-name="$t('RoleAssignmentModal.subjectTypeNameMembers')"
          primary-attribute="name"
          :remaining-attributes="['email']"
        />
      </Tab>
      <Tab :title="$t('RoleAssignmentModal.teamsTab')">
        <SubjectSelectList
          class="margin-top-2"
          primary-attribute="name"
          :subjects="teams"
          :subject-type-name="$t('RoleAssignmentModal.subjectTypeNameTeams')"
        />
      </Tab>
    </Tabs>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/mixins/modal'
import List from '@baserow/modules/core/components/List'
import SubjectSelectList from '@baserow_enterprise/components/rbac/SubjectSelectList'

export default {
  name: 'RoleAssignmentModal',
  components: { SubjectSelectList, List },
  mixins: [Modal],
  props: {
    users: {
      type: Array,
      required: false,
      default: () => [
        { name: 'alex', email: 'test@test.com' },
        { name: 'john', email: 'test2@test.com' },
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
