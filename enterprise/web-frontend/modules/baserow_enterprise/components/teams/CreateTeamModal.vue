<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('teamsSettings.createTeamModal.title') }}
    </h2>
    <Error :error="error"></Error>
    <CreateTeamForm ref="createForm" @submitted="teamSubmitted">
      <div class="col col-12 align-right">
        <button
          :class="{ 'button--loading': loading }"
          class="button"
          :disabled="loading"
        >
          {{ $t('teamsSettings.createTeamModal.submit') }}
        </button>
      </div>
    </CreateTeamForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import CreateTeamForm from '@baserow_enterprise/components/teams/CreateTeamForm'

export default {
  name: 'CreateTeamModal',
  components: { CreateTeamForm },
  mixins: [modal, error],
  props: {
    group: {
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
    async teamSubmitted(values) {
      this.createLoading = true
      this.hideError()

      try {
        const { team } = await this.$store.dispatch('team/create', {
          groupId: this.group.id,
          values,
        })
        this.loading = false
        this.$emit('created', team)
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'team')
      }
    },
  },
}
</script>
