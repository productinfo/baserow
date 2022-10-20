<template>
  <Context>
    <template v-if="Object.keys(member).length > 0">
      <div class="context__menu-title">Workspace permissions</div>
      <ul class="context__menu context__menu--can-be-active">
        <li v-for="role in roles" :key="role.value">
          <a
            :class="{ active: member.permissions === role.value }"
            @click="roleUpdate(role.value, member)"
          >
            {{ role.name }}
            <div class="context__menu-item-description">
              {{ role.description }}
            </div>
          </a>
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'
import context from '@baserow/modules/core/mixins/context'
import GroupService from '@baserow/modules/core/services/group'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { clone } from '@baserow/modules/core/utils/object'

export default {
  name: 'EditRoleContext',
  mixins: [context],
  props: {
    group: {
      required: true,
      type: Object,
    },
    member: {
      required: true,
      type: Object,
    },
    roles: {
      required: true,
      type: Array,
    },
  },
  computed: {
    ...mapGetters({
      userId: 'auth/getUserId',
    }),
  },
  methods: {
    async roleUpdate(permissionsNew, member) {
      if (member.permissions === permissionsNew) {
        return
      }

      const oldMember = clone(member)
      const newMember = clone(member)
      newMember.permissions = permissionsNew

      this.$emit('update-member', newMember)

      try {
        await GroupService(this.$client).updateUser(oldMember.id, {
          permissions: newMember.permissions,
        })
        await this.$store.dispatch('group/forceUpdateGroupUser', {
          groupId: this.group.id,
          id: oldMember.id,
          values: { permissions: newMember.permissions },
        })
      } catch (error) {
        this.$emit('update-member', oldMember)
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
