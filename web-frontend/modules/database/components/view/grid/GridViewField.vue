<template>
  <div class="grid-view-column" style="width: 200px;" @click="select($event)">
    <component
      :is="getFieldComponent(field.type)"
      ref="column"
      :field="field"
      :value="row['field_' + field.id]"
      :selected="selected"
      @update="update"
    />
  </div>
</template>

<script>
import { isElement } from '@baserow/modules/core/utils/dom'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'GridViewField',
  props: {
    table: {
      type: Object,
      required: true
    },
    field: {
      type: Object,
      required: true
    },
    row: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      /**
       * Indicates whether the field is selected.
       */
      selected: false,
      /**
       * Timestamp of the last the time the user clicked on the field. We need this to
       * check if it was double clicked.
       */
      clickTimestamp: null
    }
  },
  watch: {
    row() {
      // @TODO docs
      this.recycle()
    }
  },
  /**
   * Because the component can be destroyed if it moves out of the viewport we might
   * need to take some action if the the component is in a selected state.
   */
  beforeDestroy() {
    if (this.selected) {
      this.unselect()
    }
  },
  methods: {
    getFieldComponent(type) {
      return this.$store.getters['field/getType'](
        type
      ).getGridViewFieldComponent()
    },
    /**
     * If the grid field component emits an update event this method will be called
     * which will actually update the value via the store.
     */
    async update(value, oldValue) {
      try {
        await this.$store.dispatch('view/grid/updateValue', {
          table: this.table,
          row: this.row,
          field: this.field,
          value,
          oldValue
        })
      } catch (error) {
        this.$forceUpdate()
        notifyIf(error, 'column')
      }

      // This is needed because in some cases we do have a value yet, so a watcher of
      // the value is not guaranteed. This will make sure the component shows the
      // latest value.
      this.$forceUpdate()
    },
    /**
     * Method that is called when a user clicks on the grid field. It wil
     * @TODO improve speed somehow, maybe with the fastclick library.
     */
    select(event) {
      const timestamp = new Date().getTime()

      if (this.selected) {
        // If the field is already selected we will check if the click is a doubleclick
        // if it was within 200 ms. The double click event can be useful for components
        // because they might want to change the editing state.
        if (
          this.clickTimestamp !== null &&
          timestamp - this.clickTimestamp < 200
        ) {
          this.$refs.column.doubleClick()
        }
      } else {
        // If the field is not yet selected we can change the state to selected.
        this.selected = true
        this.$nextTick(() => {
          // Call the select method on the next tick because we want to wait for all
          // changes to have rendered.
          this.$refs.column.select()
        })

        // Register a body click event listener so that we can detect if a user has
        // clicked outside the field. If that happens we want to unselect the field and
        // possibly save the value.
        this.$el.clickOutsideEvent = event => {
          if (
            // Check if the column is still selected.
            this.selected &&
            // If the click was outside the column element.
            !isElement(this.$el, event.target)
          ) {
            this.unselect()
          }
        }
        document.body.addEventListener('click', this.$el.clickOutsideEvent)
      }

      this.clickTimestamp = timestamp
    },
    unselect() {
      this.$refs.column.beforeUnSelect()
      this.$nextTick(() => {
        this.selected = false
      })
      document.body.removeEventListener('click', this.$el.clickOutsideEvent)
    },
    recycle() {
      this.selected = false
      this.clickTimestamp = null
      this.$refs.column.recycle()
      document.body.removeEventListener('click', this.$el.clickOutsideEvent)
    }
  }
}
</script>
