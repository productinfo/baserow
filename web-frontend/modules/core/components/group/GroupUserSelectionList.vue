<template>
  <div>
    <input
      v-model="activeSearchTerm"
      type="text"
      class="input input--large"
      :placeholder="$t('GroupUserSelectionList.searchPlaceholder')"
      @keyup="search(activeSearchTerm)"
    />
    <div class="margin-top-2">
      {{
        $t('GroupUserSelectionList.selectedAmountLabel', {
          count: usersSelected.length,
        })
      }}
    </div>
    <List
      class="margin-top-2 select-members-list__items"
      :items="usersFiltered"
      :attributes="['email']"
      selectable
      @selected="userSelected"
    >
      <template #left-side="{ item }">
        <div class="select-members-list__user-initials margin-left-1">
          {{ item.name | nameAbbreviation }}
        </div>
        <span class="margin-left-1">
          {{ item.name }}
        </span>
      </template>
    </List>
    <GroupUserAssignmentModalFooter
      type="members"
      :count="usersSelected.length"
      @invite="$emit('invite', usersSelected)"
    />
  </div>
</template>

<script>
import GroupUserAssignmentModalFooter from '@baserow/modules/core/components/group/GroupUserAssignmentModalFooter'
export default {
  name: 'GroupUserSelectionList',
  components: { GroupUserAssignmentModalFooter },
  props: {
    users: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  data() {
    return {
      usersFiltered: this.users,
      usersSelected: [],
      activeSearchTerm: null,
    }
  },
  computed: {
    searchAbleAttributes() {
      return ['name', 'email']
    },
  },
  methods: {
    search(value) {
      if (value === null || value === '' || this.users.length === 0) {
        this.usersFiltered = this.users
      }

      this.usersFiltered = this.users.filter((user) =>
        this.searchAbleAttributes.some((attribute) =>
          user[attribute].includes(value)
        )
      )
    },
    userSelected({ value, item }) {
      if (value) {
        this.usersSelected.push(item)
      } else {
        const index = this.usersSelected.findIndex(
          (user) => user.id === item.id
        )
        this.usersSelected.splice(index, 1)
      }
    },
  },
}
</script>
