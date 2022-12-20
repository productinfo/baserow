<template>
  <Modal>
    <h2 class="box__title">{{  $t('auditLog.exportModalTitle') }}</h2>
    <Error :error="error"></Error>
  </Modal>
</template>

<script>
import { mapState } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import ExporterService from '@baserow/modules/database/services/export'
import ViewService from '@baserow/modules/database/services/view'
import { populateView } from '@baserow/modules/database/store/view'
import ExportTableForm from '@baserow/modules/database/components/export/ExportTableForm'
import ExportTableLoadingBar from '@baserow/modules/database/components/export/ExportTableLoadingBar'

export default {
  name: 'ExportAuditLogModal',
  components: { ExportTableForm, ExportTableLoadingBar },
  mixins: [modal, error],
  props: {
   
  },
  data() {
    return {
      loading: false,
      job: null,
      pollInterval: null,
      isValid: false,
    }
  },
  computed: {
    jobIsRunning() {
      return (
        this.job !== null && ['exporting', 'pending'].includes(this.job.status)
      )
    },
    jobHasFailed() {
      return ['failed', 'cancelled'].includes(this.job.status)
    },
    ...mapState({
      selectedTableViews: (state) => state.view.items,
    }),
  },
  methods: {
    async show(...args) {
      const show = modal.methods.show.call(this, ...args)
      this.job = null
      this.loading = false
      return show
    },
    hide(...args) {
      this.stopPollIfRunning()
      return modal.methods.hide.call(this, ...args)
    },
    
    async submitted(values) {
      if (!this.$refs.form.isFormValid()) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        const { data } = await ExporterService(this.$client).export(
          this.table.id,
          values
        )
        this.job = data
        if (this.pollInterval !== null) {
          clearInterval(this.pollInterval)
        }
        this.pollInterval = setInterval(this.getLatestJobInfo, 1000)
      } catch (error) {
        this.stopPollAndHandleError(error)
      }
    },
    async getLatestJobInfo() {
      try {
        const { data } = await ExporterService(this.$client).get(this.job.id)
        this.job = data
        if (!this.jobIsRunning) {
          this.loading = false
          this.stopPollIfRunning()
        }
        if (this.jobHasFailed) {
          const title =
            this.job.status === 'failed'
              ? this.$t('exportTableModal.failedTitle')
              : this.$t('exportTableModal.cancelledTitle')
          const message =
            this.job.status === 'failed'
              ? this.$t('exportTableModal.failedDescription')
              : this.$t('exportTableModal.cancelledDescription')
          this.showError(title, message)
        }
      } catch (error) {
        this.stopPollAndHandleError(error)
      }
    },
    stopPollAndHandleError(error) {
      this.loading = false
      this.stopPollIfRunning()
      this.handleError(error, 'export')
    },
    stopPollIfRunning() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
      }
    },
    valuesChanged() {
      this.isValid = this.$refs.form.isFormValid()
      this.job = null
    },
  },
}
</script>
