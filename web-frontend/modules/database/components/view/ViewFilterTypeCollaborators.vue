<template>
  <FieldCollaboratorDropdown
    :collaborators="availableCollaborators"
    :disabled="disabled"
    class="dropdown--floating filters__value-dropdown dropdown--tiny"
  ></FieldCollaboratorDropdown>
</template>

<script>
import FieldCollaboratorDropdown from '@baserow/modules/database/components/field/FieldCollaboratorDropdown'
import viewFilter from '@baserow/modules/database/mixins/viewFilter'
import availableCollaborators from '@baserow/modules/database/mixins/availableCollaborators'

// :value="copy"
// @input="input"

export default {
  name: 'ViewFilterTypeSelectOptions',
  components: { FieldCollaboratorDropdown },
  mixins: [viewFilter, availableCollaborators],
  computed: {
    copy() {
      const value = this.filter.value
      return value === '' ? null : parseInt(value) || null
    },
  },
  methods: {
    input(value) {
      value = value === null ? '' : value.toString()
      this.$emit('input', value)
    },
  },
}
</script>
