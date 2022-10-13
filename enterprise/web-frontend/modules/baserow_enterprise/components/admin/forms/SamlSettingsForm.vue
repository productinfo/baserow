<template>
  <form class="context__form" @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('domain')" class="control">
      <label class="control__label">{{ $t('enterprise.saml.domain') }}</label>
      <div class="control__elements">
        <input
          ref="domain"
          v-model="values.domain"
          :class="{
            'input--error': fieldHasErrors('domain') || serverErrors.domain,
          }"
          type="text"
          class="input"
          :placeholder="$t('enterprise.samlSettingsForm.domain')"
          @input="$emit('input', 'domain')"
          @blur="$v.values.domain.$touch()"
        />
        <div
          v-if="$v.values.domain.$dirty && !$v.values.domain.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
        <div
          v-else-if="
            $v.values.domain.$dirty && !$v.values.domain.mustHaveUniqueDomain
          "
          class="error"
        >
          {{ $t('enterprise.samlSettingsForm.domainAlreadyExists') }}
        </div>
        <div v-else-if="serverErrors.domain" class="error">
          {{ $t('enterprise.samlSettingsForm.invalidDomain') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('metadata')" class="control">
      <label class="control__label">{{ $t('enterprise.saml.metadata') }}</label>
      <div class="control__elements">
        <textarea
          ref="metadata"
          v-model="values.metadata"
          rows="12"
          :class="{
            'input--error': fieldHasErrors('metadata') || serverErrors.metadata,
          }"
          type="textarea"
          class="input saml-settings__metadata"
          :placeholder="$t('enterprise.samlSettingsForm.metadata')"
          @input="$emit('input', 'metadata')"
          @blur="$v.values.metadata.$touch()"
        ></textarea>
        <div
          v-if="$v.values.metadata.$dirty && !$v.values.metadata.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
        <div v-else-if="serverErrors.metadata" class="error">
          {{ $t('enterprise.samlSettingsForm.invalidMetadata') }}
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
  name: 'SamlSettingsForm',
  mixins: [form],
  props: {
    authProvider: {
      type: Object,
      required: false,
      default: () => ({}),
    },
    serverErrors: {
      type: Object,
      required: false,
      default: () => ({}),
    },
  },
  data() {
    return {
      allowedValues: ['domain', 'metadata'],
      values: {
        domain: '',
        metadata: '',
      },
    }
  },
  computed: {
    samlDomains() {
      const samlAuthProviders =
        this.$store.getters['authProviderAdmin/getAll'].saml?.authProviders ||
        []
      return samlAuthProviders
        .filter(
          (authProvider) => authProvider.domain !== this.authProvider.domain
        )
        .map((authProvider) => authProvider.domain)
    },
  },
  methods: {
    getDefaultValues() {
      return {
        domain: this.authProvider.domain || '',
        metadata: this.authProvider.metadata || '',
      }
    },
    submit() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }
      this.$emit('submit', this.values)
    },
    mustHaveUniqueDomain(domain) {
      return !this.samlDomains.includes(domain.trim())
    },
  },
  validations() {
    return {
      values: {
        domain: { required, mustHaveUniqueDomain: this.mustHaveUniqueDomain },
        metadata: { required },
      },
    }
  },
}
</script>
