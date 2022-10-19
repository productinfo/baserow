<template functional>
  <div class="data-table__more-wrapper">
    <a
      class="data-table__more"
      @click.prevent="
        listeners['edit-user'] &&
          listeners['edit-user']({
            user: props.row,
            target: $event.currentTarget,
            time: Date.now(),
          })
      "
    >
      <i class="fas fa-ellipsis-h"></i>
    </a>
  </div>
</template>

<script>
export default {
  name: 'MoreField',
  functional: true,
  props: {
    row: {
      required: true,
      type: Object,
    },
  },
}
</script>
