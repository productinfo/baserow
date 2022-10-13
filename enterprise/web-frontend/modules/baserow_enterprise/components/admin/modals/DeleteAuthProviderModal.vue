<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('enterprise.confirmDeleteAuthProviderModal.title') }}
    </h2>
    <div class="context__form-actions context__form-actions--multiple-actions">
      <a @click="$emit('cancel')">{{ $t('action.cancel') }}</a>
      <button
        class="button button--error"
        :class="{ 'button--loading': loading }"
        :disabled="loading"
        @click="deleteProvider"
      >
        {{ $t('action.delete') }}
      </button>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'DeleteAuthProviderModal',
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
    }
  },
  methods: {
    async deleteProvider() {
      this.loading = true
      try {
        await this.$store.dispatch(
          'authProviderAdmin/delete',
          this.authProvider
        )
        this.$emit('provider-deleted')
      } catch (error) {
        notifyIf(error, 'settings')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
