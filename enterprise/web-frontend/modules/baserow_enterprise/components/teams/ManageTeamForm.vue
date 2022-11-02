<template>
  <form @submit.prevent="submit">
    <h3>{{ $t('ManageTeamForm.nameTitle') }}</h3>
    <div class="row">
      <div class="col col-12">
        <FormElement :error="fieldHasErrors('name')" class="control">
          <div class="control__elements">
            <input
              ref="name"
              v-model="values.name"
              :class="{ 'input--error': fieldHasErrors('name') }"
              type="text"
              class="input"
              @blur="$v.values.name.$touch()"
            />
            <div v-if="fieldHasErrors('name')" class="error">
              {{ $t('ManageTeamForm.errorInvalidName') }}
            </div>
          </div>
        </FormElement>
      </div>
    </div>
    <div class="row">
      <div class="col col-12">
        <slot name="memberList"></slot>
      </div>
    </div>
    <div class="row">
      <div class="col col-6">
        <slot name="inviteButton"></slot>
      </div>
      <div class="col col-6 align-right">
        <slot name="submitButton"></slot>
      </div>
    </div>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'ManageTeamForm',
  mixins: [form],
  props: {
    name: {
      type: String,
      required: false,
      default: '',
    },
  },
  data() {
    return {
      loading: false,
      max_subjects: 5,
      values: {
        name: this.name,
        subjects: [],
      },
    }
  },
  validations: {
    values: {
      name: { required },
    },
  },
  mounted() {
    this.$refs.name.focus()
  },
}
</script>
