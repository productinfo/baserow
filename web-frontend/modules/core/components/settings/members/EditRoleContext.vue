<template>
  <Context>
    <template v-if="Object.keys(row).length > 0">
      <div class="context__menu-title">
        {{ $t('membersSettings.membersTable.columns.role') }}
      </div>
      <ul class="context__menu context__menu--can-be-active">
        <li v-for="role in roles" :key="role.value">
          <a
            :class="{ active: row.permissions === role.value }"
            @click="roleUpdate(role.value, row)"
          >
            {{ role.name }}
            <div class="context__menu-item-description">
              {{ role.description }}
            </div>
          </a>
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'EditRoleContext',
  mixins: [context],
  props: {
    group: {
      required: true,
      type: Object,
    },
    row: {
      required: true,
      type: Object,
    },
    roles: {
      required: true,
      type: Array,
    },
  },
  computed: {
    ...mapGetters({
      userId: 'auth/getUserId',
    }),
  },
  methods: {
    roleUpdate(permissionsNew, row) {
      if (row.permissions === permissionsNew) {
        return
      }

      this.$emit('update-role', { value: permissionsNew, row })
      this.hide()
    },
  },
}
</script>
