<template>
  <div class="member-roles-share-toggle">
    <div>
      {{ $t('MemberRolesShareToggle.label', { name }) }}
      <div class="member-roles-share-toggle__sub-label">
        {{ $t('MemberRolesShareToggle.subLabel', { totalUserAmount }) }}
      </div>
    </div>
    <switch-input
      :value="toggled"
      large
      @input="$emit('update:toggled', $event)"
    ></switch-input>
  </div>
</template>

<script>
export default {
  name: 'MemberRolesShareToggle',
  props: {
    name: {
      type: String,
      required: true,
    },
    toggled: {
      type: Boolean,
      required: false,
      default: () => false,
    },
  },
  computed: {
    totalUserAmount() {
      return 5 // TODO
    },
  },
}
</script>
