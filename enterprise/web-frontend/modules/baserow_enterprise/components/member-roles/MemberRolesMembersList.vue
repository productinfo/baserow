<template>
  <ul class="list">
    <li v-for="member in members" :key="member.user.id" class="list__item">
      <div>
        {{ member.user.name }}
      </div>
      <Dropdown
        :show-search="false"
        :value="selectRoleAssignment(member.role_assignments).role"
        @change="updateRole(member, $event)"
      >
        <DropdownItem
          v-for="role in roles"
          :key="role.id"
          :name="role.name"
          :value="role.id"
        ></DropdownItem>
      </Dropdown>
    </li>
  </ul>
</template>

<script>
const rolesMock = [
  {
    id: 'BUILDER',
    name: 'builder',
    permissions: [],
  },
  {
    id: 'VIEWER',
    name: 'viewer',
    permissions: [],
  },
]

export default {
  name: 'MemberRolesMembersList',
  props: {
    members: {
      type: Array,
      required: false,
      default: () => [],
    },
    scope: {
      type: Number,
      required: true,
    },
    scopeType: {
      type: String,
      required: true,
    },
  },
  computed: {
    roles() {
      return rolesMock
    },
  },
  methods: {
    selectRoleAssignment(roleAssignments) {
      return roleAssignments.find(
        ({ scope, scope_type: scopeType }) =>
          scope === this.scope && scopeType === this.scopeType
      )
    },
    updateRole(member, newRole) {
      const memberCopy = JSON.parse(JSON.stringify(member))
      const roleAssignment = this.selectRoleAssignment(
        memberCopy.role_assignments
      )
      const index = memberCopy.role_assignments.findIndex(
        ({ scope, scope_type: scopeType }) =>
          scope === roleAssignment.scope &&
          scopeType === roleAssignment.scope_type
      )
      memberCopy.role_assignments[index].role = newRole
      this.$store.dispatch('member/updateMember', {
        userId: member.user.id,
        values: memberCopy,
      })
    },
  },
}
</script>
