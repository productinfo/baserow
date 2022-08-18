<template functional>
  <div ref="cell" class="grid-view__cell grid-field-many-to-many__cell">
    <div class="grid-field-many-to-many__list">
      <div
        v-for="item in props.value"
        :key="item.id"
        class="field-multiple-collaborators__item"
      >
        <div v-if="props.value" class="field-multiple-collaborators__initials">
          {{ $options.methods.initial(item.name) }}
        </div>
        <div
          v-if="props.value"
          class="
            field-multiple-collaborators__name
            background-color--light-gray
          "
        >
          {{ item.name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalGridViewFieldMultipleCollaborators',
  functional: true,
  props: {
    value: {
      required: true,
      type: Array,
    },
  },
  methods: {
    initial(name) {
      return name.slice(0, 1).toUpperCase()
    },
  },
}
</script>
