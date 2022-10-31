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
    </div>
    <h3>Users</h3>
    <div class="row">
      <div class="col col-8">
        <FormElement class="control">
          <div class="control__elements">
            <input
              ref="subjectSample"
              type="text"
              class="input"
              v-model="subjectValue"
              placeholder="Optionally choose who should be part of this team."
              disabled
            />
          </div>
        </FormElement>
      </div>
      <div class="col col-4 align-right">
        <slot name="inviteButton"></slot>
      </div>
      <slot name="createButton"></slot>
    </div>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'CreateTeamForm',
  mixins: [form],
  computed: {
    subjectValue() {
      let sample_names = this.subjects.map((subject) => subject.name)
      if(sample_names.length > this.max_subjects) {
        let beyond_sample = sample_names.length - this.max_subjects
        sample_names = sample_names.splice(0, this.max_subjects)
        return sample_names.join(', ') + ` and ${beyond_sample} more`
      }
      return sample_names.join(', ')
    }
  },
  data() {
    return {
      loading: false,
      subjects: [],
      max_subjects: 5,
      values: {
        name: '',
      }
    }
  },
  validations: {
    values: {
      name: { required },
    },
  },
}
</script>
