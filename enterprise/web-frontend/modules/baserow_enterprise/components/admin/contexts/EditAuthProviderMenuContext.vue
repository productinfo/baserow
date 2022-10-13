<template>
  <Context ref="context">
    <ul class="context__menu">
      <li>
        <a @click="$emit('edit', authProvider.id)">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          {{ $t('enterprise.editAuthProviderMenuContext.edit') }}
        </a>
      </li>
      <li>
        <a @click="$emit('delete', authProvider.id)">
          <i class="context__menu-icon fas fa-fw fa-trash-alt"></i>
          {{ $t('enterprise.editAuthProviderMenuContext.delete') }}
        </a>
      </li>
      <slot></slot>
    </ul>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'EditAuthProviderMenuContext',
  components: {},
  mixins: [context],
  props: {
    authProvider: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      deleteLoading: false,
    }
  },
  methods: {
    /*
    // Allows other components to toggle the `FieldContext`
    // and then, once visible, immediately show the
    // `UpdateFieldContext` at the same time.
    showUpdateFieldContext() {
      this.$refs.updateFieldContext.toggle(
        this.$refs.updateFieldContextLink,
        'bottom',
        'left'
      )
    },
    async deleteField() {
      this.deleteLoading = true
      const { field } = this

      try {
        const { data } = await this.$store.dispatch('field/deleteCall', field)
        this.$emit('delete')
        await this.$store.dispatch('field/forceDelete', field)
        await this.$store.dispatch('field/forceUpdateFields', {
          fields: data.related_fields,
        })
        await this.$store.dispatch('notification/restore', {
          trash_item_type: 'field',
          trash_item_id: field.id,
        })
      } catch (error) {
        if (error.response && error.response.status === 404) {
          this.$emit('delete')
          await this.$store.dispatch('field/forceDelete', field)
        } else {
          notifyIf(error, 'field')
        }
      }
      this.hide()
      this.deleteLoading = false
    }, */
  },
}
</script>
