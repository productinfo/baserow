<template>
  <Context>
    <template v-if="Object.keys(team).length > 0">
      <ul class="context__menu">
        <li>
          <a @click="$emit('edit', team)">
            <i class="context__menu-icon fas fa-fw fa-pen"></i>
            {{ $t('EditTeamContext.edit') }}
          </a>
        </li>
        <li>
          <a
            :class="{
              'context__menu-item--loading': removeLoading,
            }"
            class="color-error"
            @click.prevent="remove(team)"
          >
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            {{ $t('EditTeamContext.remove') }}
          </a>
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'EditTeamContext',
  mixins: [context],
  props: {
    group: {
      required: true,
      type: Object,
    },
    team: {
      required: true,
      type: Object,
    },
  },
  data() {
    return {
      removeLoading: false,
    }
  },
  methods: {
    async remove(team) {
      if (this.removeLoading) {
        return
      }

      this.removeLoading = true

      try {
        await this.$store.dispatch('team/delete', {
          groupId: this.group.id,
          id: team.id,
          values: { team_id: team.id },
        })
        this.$emit('refresh')
        this.hide()
      } catch (error) {
        notifyIf(error)
      } finally {
        this.removeLoading = false
      }
    },
  },
}
</script>
