<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('enterprise.createSettingsAuthProviderModal.title') }}
    </h2>
    <div v-if="authProviderType">
      <component
        :is="getProviderAdminSettingsFormComponent()"
        ref="providerSettingsForm"
        :server-errors="serverErrors"
        @submit="create($event)"
        @input="updateServerErrors($event)"
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
            {{ $t('action.create') }}
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
  name: 'CreateAuthProviderModal',
  mixins: [modal],
  props: {
    authProviderType: {
      type: String,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      loading: false,
      serverErrors: {},
    }
  },
  methods: {
    getProviderAdminSettingsFormComponent() {
      return this.$registry
        .get('authProvider', this.authProviderType)
        .getAdminSettingsFormComponent()
    },
    async create(values) {
      this.loading = true
      this.serverErrors = {}
      try {
        await this.$store.dispatch('authProviderAdmin/create', {
          type: this.authProviderType,
          values,
        })
        this.$emit('created')
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
