<template>
  <li
    class="select-collaborators__dropdown-item"
    :class="{
      hidden: !isVisible(query),
      active: isActive(value),
      disabled: disabled,
      hover: isHovering(value),
    }"
  >
    <a
      class="select-collaborators__dropdown-link"
      @click="select(value, disabled)"
      @mousemove="hover(value, disabled)"
    >
      <div class="select-collaborators__initials">A</div>
      <div class="select-collaborators__dropdown-option">
        {{ name }}
      </div>
    </a>
  </li>
</template>

<script>
import dropdownItem from '@baserow/modules/core/mixins/dropdownItem'

export default {
  name: 'FieldCollaboratorDropdownItem',
  mixins: [dropdownItem],
}
</script>
