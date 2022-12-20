<template>
    <div class="audit-log__table">
    <CrudTable
    :columns="columns"
    :filters="filters"
    :defaultColumnSorts="[{key: 'timestamp', direction: 'asc'}]"
    :service="service"
    :enable-search="false"
    row-id-key="id"
  >
    <template #title>
      {{ $t('auditLog.title') }}
    </template>
    <template #header-right-side>
      <button class="button button--large" @click.preventDefault="$refs.exportModal.show()">
        {{ $t('auditLog.exportToCsv') }}
      </button>
    </template>
    <template #header-filters>
      <div class="audit-log__filters">
      <FilterWrapper :name="$t('auditLog.filterUserTitle')">
      <PaginatedDropdown
          ref="userFilter"
          :value="null"
          :fetch-page="fetchUsers"
          :not-selected-text="$t('auditLog.filterUser')"
          @input="filterUser"
        ></PaginatedDropdown>
      </FilterWrapper>
      <FilterWrapper :name="$t('auditLog.filterGroupTitle')">
        <PaginatedDropdown
          ref="groupFilter"
          :value="null"
          :fetch-page="fetchGroups"
          :not-selected-text="$t('auditLog.filterGroup')"
          @input="filterGroup"
        ></PaginatedDropdown>
      </FilterWrapper>
      <FilterWrapper :name="$t('auditLog.filterEventTypeTitle')">
        <PaginatedDropdown
          ref="typeFilter"
          :value="null"
          :fetch-page="fetchEventTypes"
          :not-selected-text="$t('auditLog.filterEventType')"
          @input="filterEventType"
        ></PaginatedDropdown>
      </FilterWrapper>
      <FilterWrapper :name="$t('auditLog.filterFromDateTitle')">
        <DateFilter
          ref="fromDateFilter"
          :value="fromDate"
          :placeholder="$t('auditLog.filterFromDate')"
          @input="filterFromDate"
        ></DateFilter>
      </FilterWrapper>
      <FilterWrapper :name="$t('auditLog.filterToDateTitle')">
        <DateFilter
          ref="toDateFilter"
          :value="toDate"
          :placeholder="$t('auditLog.filterToDate')"
          @input="filterToDate"
        ></DateFilter>
      </FilterWrapper>
      </div>
    </template>
    <template #menus="slotProps">
    </template>
  </CrudTable>
  <ExportAuditLogModal ref="exportModal"></ExportAuditLogModal>
</div>
</template>


<script>
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import PaginatedDropdown from '@baserow/modules/core/components/PaginatedDropdown'
import AuditLogAdminService from '@baserow_enterprise/services/auditLogAdmin'
import DateFilter from '@baserow_enterprise/components/crudTable/filters/DateFilter'
import FilterWrapper from '@baserow_enterprise/components/crudTable/filters/filterWrapper'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import LongTextField from '@baserow_enterprise/components/crudTable/fields/LongTextField'
import ExportAuditLogModal from '@baserow_enterprise/components/admin/modals/ExportAuditLogModal'

export default {
  name: 'AuditLogAdminTable',
  components: { CrudTable, PaginatedDropdown, DateFilter, FilterWrapper, ExportAuditLogModal},
  layout: 'app',
  middleware: 'staff',
  data() {
    this.columns = [
      new CrudTableColumn(
        'user',
        () => this.$t('auditLog.user'),
        SimpleField,
        true,
        false
      ),
      new CrudTableColumn(
        'group',
        () => this.$t('auditLog.group'),
        SimpleField,
        true,
        false
      ),
      new CrudTableColumn(
        'type',
        () => this.$t('auditLog.eventType'),
        SimpleField,
        true,
        false
      ),
      new CrudTableColumn(
        'description',
        () => this.$t('auditLog.description'),
        LongTextField,
        true,
        false,
        false,
        {},
        '20',
        ),
      new CrudTableColumn(
        'timestamp',
        () => this.$t('auditLog.timestamp'),
        LocalDateField,
        true,
        false
      ),
      new CrudTableColumn(
        'ip_address',
        () => this.$t('auditLog.ip_address'),
        SimpleField,
        true,
        false
      ),
    ]
    this.service = AuditLogAdminService(this.$client)
    return {
      filters: {},
      fromDate: null,
      toDate: null,
    }
  },
  methods: {
    setFilter(key, value) {
      if (value == null) {
       if(this.filters[key] != undefined) {
        this.filters = _.pickBy(this.filters, (v, k) => {
          return key !== k
        })
      }
      } else{
        this.filters = {...this.filters, [key]: value}
      }
    },
    filterUser(user) {
      this.setFilter('user_email', user.id)
    },
    fetchUsers(page, search) {
      return this.service.fetchUsers(page, search)
    },
    filterGroup(group) {
      this.setFilter('group_name', group.id)
    },
    fetchGroups(page, search) {
      return this.service.fetchGroups(page, search)
    },
    fetchEventTypes(page, search) {
      return this.service.fetchEventTypes(page, search)
    },
    filterEventType(eventType) {
      this.setFilter('event_type', eventType.id)
    },
    filterFromDate(date) {
      this.fromDate = date
      this.setFilter('from_date', date)
    },
    filterToDate(date) {
      this.toDate = date
      this.setFilter('to_date', date)
    },
  },
}
</script>