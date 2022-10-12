<template>
  <Modal>
    <Tabs>
      <Tab
        v-if="databaseId"
        :title="$t('MemberRolesModal.MemberRolesDatabaseTabTitle')"
        class="margin-top-3"
      >
        <MemberRolesDatabaseTab :database="database" />
      </Tab>
      <Tab
        class="margin-top-3"
        :title="$t('MemberRolesModal.MemberRolesTableTabTitle')"
      >
        <MemberRolesTableTab />
      </Tab>
    </Tabs>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/mixins/modal'
import MemberRolesDatabaseTab from '@baserow_enterprise/components/member-roles/MemberRolesDatabaseTab'
import MemberRolesTableTab from '@baserow_enterprise/components/member-roles/MemberRolesTableTab'

export default {
  name: 'MemberRolesModal',
  components: { MemberRolesTableTab, MemberRolesDatabaseTab },
  mixins: [Modal],
  props: {
    databaseId: {
      type: Number,
      required: false,
      default: () => null,
    },
  },
  computed: {
    database() {
      return this.$store.getters['application/get'](this.databaseId)
    },
  },
}
</script>
