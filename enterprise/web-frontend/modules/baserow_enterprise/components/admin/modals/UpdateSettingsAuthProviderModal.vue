<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('enterprise.updateSettingsAuthProviderModal.title') }}
    </h2>
    <div>
      <component
        :is="getProviderAdminSettingsFormComponent(authProvider)"
        ref="providerSettingsForm"
        :auth-provider="authProvider"
        :server-errors="serverErrors"
        @input="updateServerErrors($event)"
        @submit="onSettingsUpdated"
      >
        <div
          class="context__form-actions context__form-actions--multiple-actions"
        >
          <a @click="$emit('cancel')">{{ $t('action.cancel') }}</a>
          <button
            class="button"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('action.save') }}
          </button>
        </div>
      </component>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'EditAuthProviderModal',
  mixins: [modal],
  props: {
    authProvider: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      serverErrors: {},
    }
  },
  methods: {
    getProviderAdminSettingsFormComponent(provider) {
      return this.$registry
        .get('authProvider', provider.type)
        .getAdminSettingsFormComponent()
    },
    async onSettingsUpdated(values) {
      this.loading = true
      try {
        await this.$store.dispatch('authProviderAdmin/update', {
          authProvider: this.authProvider,
          values,
        })
        this.$emit('settings-updated')
      } catch (error) {
        const rspData = error.response?.data || {}
        if (rspData.error === 'ERROR_REQUEST_BODY_VALIDATION') {
          for (const [key, value] of Object.entries(rspData.detail || {})) {
            this.serverErrors[key] = value
          }
        } else {
          notifyIf(error, 'settings')
        }
      } finally {
        this.loading = false
      }
    },
    updateServerErrors(fieldName) {
      this.serverErrors[fieldName] = null
    },
  },
}
</script>
