<template>
    <CrudTable
    :columns="columns"
    :defaultColumnSorts="[{key: 'timestamp', direction: 'asc'}]"
    :service="service"
    row-id-key="id"
    @row-context="onRowContext"
  >
    <template #title>
      {{ $t('auditLog.title') }}
    </template>
    <template #menus="slotProps">
    </template>
  </CrudTable>
</template>


<script>
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import AuditLogAdminService from '@baserow_enterprise/services/auditLogAdmin'
import UsernameField from '@baserow_premium/components/admin/users/fields/UsernameField'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import GroupNameField from '@baserow_premium/components/admin/groups/fields/GroupNameField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'

export default {
  name: 'AuditLogAdminTable',
  components: { CrudTable },
  layout: 'app',
  middleware: 'staff',
  data() {
    this.columns = [
      new CrudTableColumn(
        'rendered_user',
        () => this.$t('auditLog.user'),
        SimpleField,
        true,
        true
      ),
      new CrudTableColumn(
        'rendered_group',
        () => this.$t('auditLog.group'),
        SimpleField,
        true,
        true
      ),
      new CrudTableColumn(
        'event_type',
        () => this.$t('auditLog.eventType'),
        SimpleField,
        true,
        true
      ),
      new CrudTableColumn(
        'description',
        () => this.$t('auditLog.description'),
        SimpleField,
        true,
        true
        ),
      new CrudTableColumn(
        'timestamp',
        () => this.$t('auditLog.timestamp'),
        SimpleField,
        true,
        true
      ),
      new CrudTableColumn(
        'ip_address',
        () => this.$t('auditLog.ip_address'),
        SimpleField,
        true,
        true
      ),
    ]
    this.service = AuditLogAdminService(this.$client)
    return {}
  },
  methods: {
    onRowContext({ row, event, target }) {
      event.preventDefault()
      if (target === undefined) {
        target = {
          left: event.clientX,
          top: event.clientY,
        }
      }

      const action = row.id === this.editGroup.id ? 'toggle' : 'show'
      this.editGroup = row
      this.$refs.editGroupContext[action](target, 'bottom', 'left', 4)
    },
  },
}
</script>