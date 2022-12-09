<template>
  <i v-tooltip="tooltip" class="help_icon fas fa-question-circle"> </i>
</template>

<script>
export default {
  name: 'HelpIcon',
  props: {
    tooltip: {
      type: String,
      required: false,
      default: null,
    },
  },
}
</script>
