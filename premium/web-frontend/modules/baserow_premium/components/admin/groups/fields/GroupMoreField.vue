<template functional>
  <div class="data-table__more-wrapper">
    <a
      class="data-table__more"
      @click.prevent="
        listeners['edit-group'] &&
          listeners['edit-group']({
            group: props.row,
            target: $event.currentTarget,
          })
      "
    >
      <i class="fas fa-ellipsis-h"></i>
    </a>
  </div>
</template>

<script>
export default {
  name: 'GroupMoreField',
  functional: true,
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
}
</script>
