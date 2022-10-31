<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('teamsSettings.createTeamModal.title') }}
    </h2>
    <Error :error="error"></Error>
    <CreateTeamForm ref="createForm" @submitted="teamSubmitted">
      <template #inviteButton>
        <a
          :class="{ 'button--loading': loading }"
          class="button"
          :disabled="loading"
          @click="$refs.groupUserAssignmentModal.show()"
          >{{ $t('MemberRolesDatabaseTab.selectMembers') }}
      </a>
      </template>
      <template #createButton>
        <div class="col col-12 align-right">
          <button
            :class="{ 'button--loading': loading }"
            class="button"
            :disabled="loading"
          >
            {{ $t('teamsSettings.createTeamModal.submit') }}
          </button>
        </div>
      </template>
    </CreateTeamForm>
    <GroupUserAssignmentModal
      ref="groupUserAssignmentModal"
      :users="getAllUsers"
      @invite="storeSelectedUsers"
     />
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import CreateTeamForm from '@baserow_enterprise/components/teams/CreateTeamForm'

import { mapGetters } from 'vuex'
import GroupUserAssignmentModal from '@baserow/modules/core/components/group/GroupUserAssignmentModal'

export default {
  name: 'CreateTeamModal',
  components: { CreateTeamForm, GroupUserAssignmentModal },
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
      subjectSelections: []
    }
  },
  created() {
    this.$store.dispatch('group/fetchAllGroupUser', {
      groupId: this.group.id
    })
  },
  computed: {
    ...mapGetters({
      members: 'group/getAllUsers',
    }),
    getAllUsers() {
      return Object.values(this.members)
    }
  },
  methods: {
    async show(...args) {
      this.hideError()
      modal.methods.show.bind(this)(...args)
    },
    storeSelectedUsers(selections) {
      selections.push({name: 'Alex'})
      selections.push({name: 'Bram'})
      selections.push({name: 'Jérémie'})
      selections.push({name: 'Nigel'})
      selections.push({name: 'Petr'})
      selections.push({name: 'Clive'})
      selections.push({name: 'Barry'})
        this.subjectSelections = selections
        this.$refs.createForm.subjects = selections
    },
    async teamSubmitted(values) {
      this.createLoading = true
      this.hideError()
      
      if(this.subjectSelections.length) {
        values['subjects'] = []
        for(let s = 0; s < this.subjectSelections.length; s++) {
          values['subjects'].push({
              subject_id: this.subjectSelections[s].user_id,
              subject_type: "auth_user"
          })
        }
      }
      console.log(values)

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
        this.handleError(error, 'team', {
          ERROR_TEAM_NAME_NOT_UNIQUE: new ResponseErrorMessage(
            this.$t('teamsSettings.createTeamModalInvalidNameTitle'),
            this.$t('teamsSettings.createTeamModalInvalidNameMessage')
          ),
        })
      }
    },
  },
}
</script>
