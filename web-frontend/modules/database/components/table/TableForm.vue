<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control-label">
        <i class="fas fa-font"></i>
        Name
      </label>
      <div class="control-elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input-error': $v.values.name.$error }"
          type="text"
          class="input input-large"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="$v.values.name.$error" class="error">
          This field is required.
        </div>
      </div>
    </div>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'TableForm',
  mixins: [form],
  data() {
    return {
      values: {
        name: ''
      }
    }
  },
  validations: {
    values: {
      name: { required }
    }
  },
  mounted() {
    this.$refs.name.focus()
  }
}
</script>
