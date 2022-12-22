<template>
  <Modal>
    <h2 class="box__title">{{ $t('exportAuditLogModal.exportModalTitle') }}</h2>
    <Error :error="error"></Error>
    <ExportAuditLogForm ref="form" :loading=loading @submitted="submitted">
      <ExportTableLoadingBar :job="job" :loading="loading" :filename="filename" :disabled="false">
      </ExportTableLoadingBar>
    </ExportAuditLogForm>
  </Modal>
</template>

<script>
import { mapState } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

import AuditLogAdminService from '@baserow_enterprise/services/auditLogAdmin'

import ExportTableLoadingBar from '@baserow/modules/database/components/export/ExportTableLoadingBar'
import ExportAuditLogForm from '@baserow_enterprise/components/admin/forms/ExportAuditLogForm'

export default {
  name: 'ExportAuditLogModal',
  components: { ExportAuditLogForm, ExportTableLoadingBar },
  mixins: [modal, error],
  props: {
    filters: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      job: null,
      pollInterval: null,
      filename: null,
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
        const { data } = await AuditLogAdminService(this.$client).startExportCsvJob(
          { ...this.filters, ...values }
        )
        this.job = data
        if (this.pollInterval !== null) {
          clearInterval(this.pollInterval)
        }
        this.pollInterval = setInterval(this.getJobInfo, 1000)
      } catch (error) {
        this.stopPollAndHandleError(error)
      }
    },
    async getJobInfo() {
      try {
        const { data } = await AuditLogAdminService(this.$client).getJobInfo(this.job.id)
        this.job = data
        console.log(this.job, this.jobIsRunning)
        if (!this.jobIsRunning) {
          this.loading = false
          this.stopPollIfRunning()
        }
        if (this.jobHasFailed) {
          let title, message
          if (job.status === 'failed') {
            title = this.$t('exportAuditLogModal.failedTitle')
            message = this.$t('exportAuditLogModal.failedDescription')
          } else {  // cancelled
            title = this.$t('exportAuditLogModal.cancelledTitle')
            message = this.$t('exportAuditLogModal.cancelledDescription')
          }
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
