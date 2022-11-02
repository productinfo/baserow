<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('CreateTeamModal.title') }}
    </h2>
    <Error :error="error"></Error>
    <ManageTeamForm ref="manageForm" @submitted="createTeam">
      <template #inviteButton>
        <a
          v-if="uninvitedUserSubjects.length"
          :class="{ 'button--loading': loading }"
          class="button button--ghost"
          :disabled="loading"
          @click="$refs.groupUserAssignmentModal.show()"
          >{{ $t('CreateTeamModal.inviteMembers') }}
        </a>
      </template>
      <template #memberList>
        <h3>{{ $t('ManageTeamForm.usersTitle') }}</h3>
        <span v-if="!invitedUserSubjects.length">{{
          $t('CreateTeamModal.NoSubjectsSelected', {
            buttonLabel: $t('CreateTeamModal.inviteMembers'),
          })
        }}</span>
        <List
          v-if="invitedUserSubjects"
          class="margin-top-2 select-members-list__items"
          :items="invitedUserSubjects"
          :attributes="[]"
        >
          <template #left-side="{ item }">
            <div class="select-members-list__user-initials margin-left-1">
              {{ item.name | nameAbbreviation }}
            </div>
            <span class="margin-left-1">
              {{ item.name }}
            </span>
          </template>
          <template #right-side="{ item }">
            <div class="margin-right-1">
              {{ item.email }}
              <a class="color-error" @click="removeSubject(item)"
                ><i class="fas fa-fw fa-trash"></i
              ></a>
            </div>
          </template>
        </List>
      </template>
      <template #submitButton>
        <button
          :class="{ 'button--loading': loading }"
          class="button"
          :disabled="loading"
        >
          {{ $t('CreateTeamModal.submit') }}
        </button>
      </template>
    </ManageTeamForm>
    <GroupUserAssignmentModal
      ref="groupUserAssignmentModal"
      :users="uninvitedUserSubjects"
      @invite="storeSelectedUsers"
    />
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import ManageTeamForm from '@baserow_enterprise/components/teams/ManageTeamForm'
import TeamService from '@baserow_enterprise/services/team'

import { mapGetters } from 'vuex'
import GroupUserAssignmentModal from '@baserow/modules/core/components/group/GroupUserAssignmentModal'

export default {
  name: 'CreateTeamModal',
  components: { ManageTeamForm, GroupUserAssignmentModal },
  mixins: [modal, error],
  props: {
    team: {
      type: Object,
      required: false,
      default: () => {},
    },
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      invitedUserSubjects: [], // All members we're inviting to the team.
      uninvitedUserSubjects: [], // All uninvited members in the group.
    }
  },
  computed: {
    ...mapGetters({
      members: 'group/getAllUsers',
    }),
  },
  created() {
    this.$store.dispatch('group/fetchAllGroupUser', {
      groupId: this.group.id,
    })
  },
  methods: {
    show(...args) {
      this.hideError()
      // Reset the array of invited subjects.
      this.invitedUserSubjects = []
      // Set the initial array of subjects available for invitation.
      this.uninvitedUserSubjects = Object.values(this.members)
      modal.methods.show.bind(this)(...args)
    },
    removeSubject(removal) {
      // Re-add the member as an uninvited subject.
      this.uninvitedUserSubjects.push(removal)
      // Remove them as an invited subject.
      this.invitedUserSubjects = this.invitedUserSubjects.filter(
        (subj) => subj.user_id !== removal.user_id
      )
    },
    storeSelectedUsers(selections) {
      // Pluck out the user IDs in the objects of the `selections` array.
      const selectionsUserIds = selections.map((selection) => selection.user_id)
      // Merge the new members into `invitedUserSubjects`.
      this.invitedUserSubjects = this.invitedUserSubjects.concat(selections)
      // Remove these new selections from `uninvitedUserSubjects`.
      this.uninvitedUserSubjects = this.uninvitedUserSubjects.filter(
        (member) => !selectionsUserIds.includes(member.user_id)
      )
    },
    async createTeam(values) {
      this.loading = true
      this.hideError()

      // If we have invited subjects (note: this can be a mix of pending and
      // already persisted actors), build an array of subject ID/type objects.
      if (this.invitedUserSubjects.length) {
        values.subjects = []
        for (let s = 0; s < this.invitedUserSubjects.length; s++) {
          values.subjects.push({
            subject_id: this.invitedUserSubjects[s].user_id,
            subject_type: 'auth_user',
          })
        }
      }

      try {
        const { team } = await TeamService(this.$client).create(
          this.group.id,
          values
        )
        this.loading = false
        this.$emit('created', team)
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'team', {
          ERROR_TEAM_NAME_NOT_UNIQUE: new ResponseErrorMessage(
            this.$t('CreateTeamModal.InvalidNameTitle'),
            this.$t('CreateTeamModal.InvalidNameMessage')
          ),
        })
      }
    },
  },
}
</script>
