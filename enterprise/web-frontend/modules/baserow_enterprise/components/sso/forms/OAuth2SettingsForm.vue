<template>
  <form class="context__form" @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">{{ $t('enterprise.sso.providerName') }}</label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name') }"
          type="text"
          class="input"
          :placeholder="$t('fieldForm.providerName')"
          @blur="$v.values.name.$touch()"
        />
        <div
          v-if="$v.values.name.$dirty && !$v.values.name.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('client_id')" class="control">
      <label class="control__label">{{ $t('enterprise.sso.clientId') }}</label>
      <div class="control__elements">
        <input
          ref="client_id"
          v-model="values.client_id"
          :class="{ 'input--error': fieldHasErrors('client_id') }"
          type="text"
          :placeholder="$t('fieldForm.clientId')"
          @blur="$v.values.client_id.$touch()"
        ></input>
        <div
          v-if="$v.values.client_id.$dirty && !$v.values.client_id.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('secret')" class="control">
      <label class="control__label">{{ $t('enterprise.sso.secret') }}</label>
      <div class="control__elements">
        <input
          ref="secret"
          v-model="values.secret"
          :class="{ 'input--error': fieldHasErrors('secret') }"
          type="text"
          :placeholder="$t('fieldForm.secret')"
          @blur="$v.values.secret.$touch()"
        ></input>
        <div
          v-if="$v.values.secret.$dirty && !$v.values.secret.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'SAMLProviderSettingsForm',
  mixins: [form],
  props: {
    provider: {
      type: Object,
      required: false,
      default: () => ({}),
    },
  },
  data() {
    return {
      allowedValues: ['name', 'client_id', 'secret'],
      values: {
        name: '',
        client_id: '',
        secret: '',
      },
    }
  },
  methods: {
    getDefaultValues() {
      return {
        name: this.provider.name || '',
        client_id: this.provider.client_id || '',
        secret: this.provider.secret || '',
      }
    },
    submit() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }
      this.$emit('submit', this.values)
    },
  },
  validations() {
    return {
      values: {
        name: {},
        client_id: { required },
        secret: { required },
      },
    }
  },
}
</script>
