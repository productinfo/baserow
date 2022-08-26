<template functional>
  <div class="card-multiple-collaborators__list-wrapper">
    <div class="card-multiple-collaborators__list">
      <div
        v-for="item in props.value"
        :key="item.id"
        class="card-multiple-collaborators__item"
      >
        <span
          class="
            field-multiple-collaborators__name
            background-color--light-gray
          "
          >{{ $options.methods.getCollaboratorName(item, parent.$store) }}</span
        >
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
  height: 30,
  mixins: [collaboratorName],
}
</script>
