<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('UpdateTeamModal.title', { teamName: team.name }) }}
    </h2>
    <Error :error="error"></Error>
    <ManageTeamForm ref="manageForm" :name="team.name" @submitted="updateTeam">
      <template #inviteButton>
        <a
          v-if="uninvitedUserSubjects.length"
          :class="{ 'button--loading': loading }"
          class="button button--ghost"
          :disabled="loading"
          @click="$refs.groupUserAssignmentModal.show()"
          >{{ $t('UpdateTeamModal.inviteMembers') }}
        </a>
      </template>
      <template #memberList>
        <h3>{{ $t('ManageTeamForm.usersTitle') }}</h3>
        <span v-if="!invitedUserSubjects.length">{{
          $t('UpdateTeamModal.NoSubjectsSelected', {
            buttonLabel: $t('UpdateTeamModal.inviteMembers'),
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
          {{ $t('UpdateTeamModal.submit') }}
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
  name: 'UpdateTeamModal',
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
      invitedUserSubjects: [], // All invited members in the group and team.
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
      this.parseSubjectsAndMembers()
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
    async parseSubjectsAndMembers() {
      // When the modal displays, fetch all current subjects in this team.
      const { data } = await TeamService(this.$client).fetchAllSubjects(
        this.team.id
      )
      const teamSubjects = data

      // Pluck out the users in the `this.members` object.
      const members = Object.values(this.members)

      // Extract the subjects which are Users.
      const userSubjects = teamSubjects.filter(
        (subject) => subject.subject_type === 'auth_user'
      )
      // Extract the user subject PKs.
      const userIds = userSubjects.map((subject) => subject.subject_id)

      // Using those user PKs, find the members records in `this.members`.
      const invitedMembers = members.filter((member) =>
        userIds.includes(member.user_id)
      )
      // Assign `invitedUserSubjects` our list of GroupUser records who are NOT subjects in this team.
      this.invitedUserSubjects = invitedMembers

      // Using those user PKs, find the members records NOT in `this.members`.
      const uninvitedMembers = members.filter(
        (member) => !userIds.includes(member.user_id)
      )
      // Assign `uninvitedUserSubjects` our list of GroupUser records who are NOT subjects in this team.
      this.uninvitedUserSubjects = uninvitedMembers
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
    async updateTeam(values) {
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
        const { data } = await TeamService(this.$client).update(
          this.team.id,
          values
        )
        this.loading = false
        this.$emit('updated', data)
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'team', {
          ERROR_TEAM_NAME_NOT_UNIQUE: new ResponseErrorMessage(
            this.$t('UpdateTeamModal.InvalidNameTitle'),
            this.$t('UpdateTeamModal.InvalidNameMessage')
          ),
        })
      }
    },
  },
}
</script>
