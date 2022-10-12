<template>
  <div>
    <div class="member-roles-database-tab__header">
      <h2>
        {{
          $t('MemberRolesDatabaseTab.title', { databaseName: database.name })
        }}
      </h2>
      <a
        class="button button--ghost"
        @click="$refs.roleAssignmentModal.show()"
        >{{ $t('MemberRolesDatabaseTab.selectMembers') }}</a
      >
    </div>
    <span class="member-roles-database-tab__everyone_access_label">
      {{ descriptionText }}
    </span>
    <member-roles-share-toggle
      :name="database.name"
      :toggled.sync="isSharedWithEveryone"
    />
    <member-roles-members-list
      :members="databaseMembers"
      scope-type="database"
      :scope="scope"
    />
    <role-assignment-modal ref="roleAssignmentModal" />
  </div>
</template>

<script>
import MemberRolesMembersList from '@baserow_enterprise/components/member-roles/MemberRolesMembersList'
import MemberRolesShareToggle from '@baserow_enterprise/components/member-roles/MemberRolesShareToggle'
import { mapGetters } from 'vuex'
import RoleAssignmentModal from '@baserow_enterprise/components/member-roles/RoleAssignmentModal'

export default {
  name: 'MemberRolesDatabaseTab',
  components: {
    RoleAssignmentModal,
    MemberRolesShareToggle,
    MemberRolesMembersList,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      isSharedWithEveryone: false,
    }
  },
  computed: {
    ...mapGetters({
      members: 'member/getMembers',
    }),
    scope() {
      return this.database.id || null
    },
    scopeType() {
      return 'database'
    },
    databaseMembers() {
      return this.members.filter((member) => {
        return member.role_assignments.some(
          ({ scope, scope_type: scopeType }) =>
            scope === this.scope && scopeType === this.scopeType
        )
      })
    },
    descriptionText() {
      return this.isSharedWithEveryone
        ? this.$t('MemberRolesDatabaseTab.everyoneHasAccess', {
            databaseName: this.database.name,
          })
        : this.$t('MemberRolesDatabaseTab.onlyYouHaveAccess')
    },
  },
  created() {
    this.$store.dispatch('member/fetchMembers')
  },
}
</script>
