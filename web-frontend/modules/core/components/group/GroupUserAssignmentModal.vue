<template>
  <Modal>
    <GroupUserSelectionList
      ref="groupUserSelectionList"
      class="margin-top-2"
      :users="users"
      @invite="storeSelectedUsers"
    />
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/mixins/modal'
import GroupUserSelectionList from '@baserow/modules/core/components/group/GroupUserSelectionList'

export default {
  name: 'GroupUserAssignmentModal',
  components: { GroupUserSelectionList },
  mixins: [Modal],
  props: {
    users: {
      type: Array,
      required: true,
    },
  },
  methods: {
    storeSelectedUsers(usersSelected) {
      this.$emit('invite', usersSelected)
      this.hide()
    },
  },
}
</script>
