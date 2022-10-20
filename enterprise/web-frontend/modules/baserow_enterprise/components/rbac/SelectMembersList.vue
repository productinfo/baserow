<template>
  <div>
    <input
      v-model="activeSearchTerm"
      type="text"
      class="input input--large"
      :placeholder="$t('SelectMembersList.searchPlaceholder')"
      @keyup="search(activeSearchTerm)"
    />
    <div class="margin-top-2">
      {{
        $t('SelectMembersList.selectedAmountLabel', {
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
        <span class="margin-left-1">
          {{ item.name }}
        </span>
      </template>
    </List>
    <SelectListFooter
      type="members"
      :count="usersSelected.length"
      :show-role-selector="showRoleSelector"
      @invite="$emit('invite', usersSelected)"
    />
  </div>
</template>

<script>
import SelectListFooter from '@baserow_enterprise/components/rbac/SelectListFooter'
export default {
  name: 'SelectMembersList',
  components: { SelectListFooter },
  props: {
    users: {
      type: Array,
      required: false,
      default: () => [],
    },
    showRoleSelector: {
      type: Boolean,
      default: false,
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
