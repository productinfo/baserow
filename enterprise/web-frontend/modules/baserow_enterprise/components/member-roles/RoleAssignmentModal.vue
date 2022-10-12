<template>
  <Modal>
    <Tabs>
      <Tab> Members </Tab>
      <Tab> Teams </Tab>
    </Tabs>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/mixins/modal'

export default {
  name: 'RoleAssignmentModal',
  mixins: [Modal],
}
</script>
