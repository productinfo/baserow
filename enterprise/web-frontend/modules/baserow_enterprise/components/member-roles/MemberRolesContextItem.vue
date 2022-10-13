<template>
  <div>
    <div @click="() => $refs.modal.show()">
      <a>
        <i class="context__menu-icon fas fa-fw fa-book"></i
        >{{ $t('MemberRolesContexItem.label') }}</a
      >
    </div>
    <MemberRolesModal ref="modal" :database-id="application.id" />
  </div>
</template>

<script>
import MemberRolesModal from '@baserow_enterprise/components/member-roles/MemberRolesModal'

export default {
  name: 'MemberRolesContextItem',
  components: { MemberRolesModal },
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
}
</script>
