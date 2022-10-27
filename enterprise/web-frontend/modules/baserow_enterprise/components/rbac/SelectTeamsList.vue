<template>
  <div>
    <input
      v-model="activeSearchTerm"
      type="text"
      class="input input--large"
      :placeholder="$t('SelectTeamsList.searchPlaceholder')"
      @keyup="search(activeSearchTerm)"
    />
    <div class="margin-top-2">
      {{
        $t('SelectTeamsList.selectedAmountLabel', {
          count: teamsSelected.length,
        })
      }}
    </div>
    <List
      class="margin-top-2 select-teams-list__items"
      :items="teamsFiltered"
      selectable
      @selected="teamSelected"
    >
      <template #left-side="{ item }">
        <span class="margin-left-1">
          {{ item.name }}
        </span>
      </template>
    </List>
    <SelectListFooter
      type="teams"
      :count="teamsSelected.length"
      :show-role-selector="showRoleSelector"
      @invite="$emit('invite', teamsSelected)"
    />
  </div>
</template>

<script>
import SelectListFooter from '@baserow_enterprise/components/rbac/SelectListFooter'
export default {
  name: 'SelectTeamsList',
  components: { SelectListFooter },
  props: {
    teams: {
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
      teamsFiltered: this.teams,
      teamsSelected: [],
      activeSearchTerm: null,
    }
  },
  computed: {
    searchAbleAttributes() {
      return ['name']
    },
  },
  methods: {
    search(value) {
      if (value === null || value === '' || this.teams.length === 0) {
        this.teamsFiltered = this.teams
      }

      this.teamsFiltered = this.teams.filter((user) =>
        this.searchAbleAttributes.some((attribute) =>
          user[attribute].includes(value)
        )
      )
    },
    teamSelected({ value, item }) {
      if (value) {
        this.teamsSelected.push(item)
      } else {
        const index = this.teamsSelected.findIndex(
          (team) => team.id === item.id
        )
        this.teamsSelected.splice(index, 1)
      }
    },
  },
}
</script>
