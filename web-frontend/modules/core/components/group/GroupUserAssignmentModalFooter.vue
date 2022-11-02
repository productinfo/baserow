<template>
  <div class="select-list-footer select-list-footer--single">
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
  name: 'GroupUserAssignmentModalFooter',
  props: {
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
