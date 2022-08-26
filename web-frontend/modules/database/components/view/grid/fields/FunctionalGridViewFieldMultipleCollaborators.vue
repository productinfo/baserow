<template functional>
  <div ref="cell" class="grid-view__cell grid-field-many-to-many__cell">
    <div class="grid-field-many-to-many__list">
      <div
        v-for="item in props.value"
        :key="item.id"
        class="field-multiple-collaborators__item"
      >
        <div
          v-if="props.value"
          class="
            field-multiple-collaborators__name
            background-color--light-gray
          "
        >
          {{ $options.methods.getCollaboratorName(item, parent.$store) }}
        </div>
        <div v-if="props.value" class="field-multiple-collaborators__initials">
          {{
            $options.methods.getCollaboratorNameInitials(item, parent.$store)
          }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import collaboratorName from '@baserow/modules/database/mixins/collaboratorName'

export default {
  name: 'FunctionalGridViewFieldMultipleCollaborators',
  functional: true,
  mixins: [collaboratorName],
  props: {
    value: {
      required: true,
      type: Array,
    },
  },
}
</script>
