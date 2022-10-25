<template>
  <form class="context__form" @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">{{ $t('oauthSettingsForm.providerName') }}</label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name')}"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.providerNamePlaceholder')"
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
    <FormElement :error="fieldHasErrors('url')" class="control">
      <label class="control__label">{{ $t('oauthSettingsForm.url') }}</label>
      <div class="control__elements">
        <input
          ref="url"
          v-model="values.url"
          :class="{ 'input--error': fieldHasErrors('url') }"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.urlPlaceholder')"
          @blur="$v.values.url.$touch()"
        ></input>
        <div
          v-if="$v.values.url.$dirty && !$v.values.url.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('client_id')" class="control">
      <label class="control__label">{{ $t('oauthSettingsForm.clientId') }}</label>
      <div class="control__elements">
        <input
          ref="client_id"
          v-model="values.client_id"
          :class="{ 'input--error': fieldHasErrors('client_id') }"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.clientIdPlaceholder')"
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
      <label class="control__label">{{ $t('oauthSettingsForm.secret') }}</label>
      <div class="control__elements">
        <input
          ref="secret"
          v-model="values.secret"
          :class="{ 'input--error': fieldHasErrors('secret') }"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.secretPlaceholder')"
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
import { required, url } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'GitLabSettingsForm',
  mixins: [form],
  props: {
    authProvider: {
      type: Object,
      required: false,
      default: () => ({}),
    },
  },
  data() {
    return {
      allowedValues: ['name', 'url', 'client_id', 'secret'],
      values: {
        name: '',
        url: '',
        client_id: '',
        secret: '',
      },
    }
  },
  methods: {
    getDefaultValues() {
      return {
        name: this.providerName,
        url: this.authProvider.url || '',
        client_id: this.authProvider.client_id || '',
        secret: this.authProvider.secret || '',
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
  computed: {
    providerName() {
      return this.$registry
          .get('authProvider', 'gitlab')
          .getProviderName(this.authProvider)
    }
  },
  validations() {
    return {
      values: {
        name: { required },
        url: { url },
        client_id: { required },
        secret: { required },
      },
    }
  },
}
</script>
