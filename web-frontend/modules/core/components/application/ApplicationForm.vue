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
  name: 'ApplicationForm',
  mixins: [form],
  data() {
    return {
      values: {
        name: ''
      }
    }
  },
  mounted() {
    this.$refs.name.focus()
  },
  validations: {
    values: {
      name: { required }
    }
  }
}
</script>
