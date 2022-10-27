<template>
  <div
    class="select-list-footer"
    :class="{ 'select-list-footer--single': !showRoleSelector }"
  >
    <div v-if="showRoleSelector">ROLE SELECTOR PLACEHOLDER</div>
    <a
      class="button"
      :class="{ disabled: !inviteEnabled }"
      @click="inviteEnabled ? $emit('invite') : null"
      >{{
        $t('SelectListFooter.invite', {
          count,
          type: $t(`SelectListFooter.types.${type}`),
        })
      }}
    </a>
  </div>
</template>

<script>
export default {
  name: 'SelectListFooter',
  props: {
    showRoleSelector: {
      type: Boolean,
      default: false,
    },
    count: {
      type: Number,
      required: true,
    },
    type: {
      type: String,
      validator: (type) => type === 'teams' || 'members',
      default: 'members',
    },
  },
  computed: {
    inviteEnabled() {
      return this.count !== 0
    },
  },
}
</script>
