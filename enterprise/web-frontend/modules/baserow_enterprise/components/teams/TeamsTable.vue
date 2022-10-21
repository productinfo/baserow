<template>
  <div>
    <CrudTable
      ref="crudTable"
      :service="service"
      :columns="columns"
      row-id-key="id"
      @row-context="onRowContext"
      @rows-update="teamCount = $event.length"
    >
      <template #title>
        {{
          $t('teamsSettings.teamsTable.title', {
            teamCount: teamCount,
            groupName: group.name,
          })
        }}
      </template>
      <template #header-right-side>
        <div
          class="button margin-left-2 button--large"
          @click="$refs.createModal.show()"
        >
          {{ $t('teamsSettings.teamsTable.createNew') }}
        </div>
      </template>
      <template #menus>
        <EditTeamContext
          ref="editTeamContext"
          :group="group"
          :team="editTeam"
          @refresh="refresh"
        ></EditTeamContext>
      </template>
    </CrudTable>
    <CreateTeamModal
      ref="createModal"
      :group="group"
      @created="refresh"
    ></CreateTeamModal>
  </div>
</template>

<script>
import CreateTeamModal from '@baserow_enterprise/components/teams/CreateTeamModal'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import TeamService from '@baserow_enterprise/services/team'
import { mapGetters } from 'vuex'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import EditTeamContext from '@baserow_enterprise/components/teams/EditTeamContext'

export default {
  name: 'TeamsTable',
  components: {
    CrudTable,
    EditTeamContext,
    CreateTeamModal,
  },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      editTeam: {},
      teamCount: 0,
    }
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
    service() {
      const service = TeamService(this.$client)
      const options = {
        ...service.options,
        urlParams: { groupId: this.group.id },
      }
      return {
        ...service,
        options,
      }
    },
    columns() {
      let columns = [
        new CrudTableColumn(
          'name',
          this.$t('teamsSettings.teamsTable.columns.name'),
          SimpleField,
          true,
          true
        ),
        new CrudTableColumn(
          'created_on',
          this.$t('teamsSettings.teamsTable.columns.created_on'),
          LocalDateField,
          true
        ),
        new CrudTableColumn(
          'subject_count',
          this.$t('teamsSettings.teamsTable.columns.subjects'),
          SimpleField,
          true
        ),
        new CrudTableColumn(null, null, MoreField, false, false, true),
      ]
      return columns
    },
  },
  methods: {
    onRowContext({ row, event, target }) {
      if (target === undefined) {
        target = {
          left: event.clientX,
          top: event.clientY,
        }
      }

      const action = row.id === this.editTeam.id ? 'toggle' : 'show'
      this.editTeam = row
      this.$refs.editTeamContext[action](target, 'bottom', 'left', 4)
    },
    async refresh() {
      await this.$refs.crudTable.fetch()
    },
  },
}
</script>
