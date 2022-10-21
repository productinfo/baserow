<template>
  <form @submit.prevent="submit">
    <h3>{{ $t('teamsSettings.createTeamForm.title') }}</h3>
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
              {{ $t('teamsSettings.createTeamForm.errorInvalidName') }}
            </div>
          </div>
        </FormElement>
      </div>
      <slot></slot>
    </div>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'CreateTeamForm',
  mixins: [form],
  data() {
    return {
      loading: false,
      values: {
        name: '',
      },
    }
  },
  validations: {
    values: {
      name: { required },
    },
  },
}
</script>
