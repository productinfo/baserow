import { onClickOutside } from '@baserow/modules/core/utils/dom'
import baseField from '@baserow/modules/database/mixins/baseField'
import copyPasteHelper from '@baserow/modules/database/mixins/copyPasteHelper'

/**
 * A mixin that can be used by a field grid component. It introduces the props that
 * will be passed by the GridViewField component and it created methods that are
 * going to be called.
 */
export default {
  mixins: [baseField, copyPasteHelper],
  props: {
    /**
     * Indicates if the grid field is in a selected state.
     */
    selected: {
      type: Boolean,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      /**
       * Timestamp of the last the time the user clicked on the field. We need this to
       * check if it was double clicked.
       */
      clickTimestamp: null,
    }
  },
  watch: {
    /**
     * It could happen that the cell is not select, but still being kept alive to
     * finish a task. This for example happens when the user selects another cell
     * while still uploading a file. When the selected state changes, we do want to
     * add and remove the event listeners to prevent conflicts.
     */
    selected(value) {
      if (value) {
        this._select()
      } else {
        this._beforeUnSelect()
      }
    },
  },
  mounted() {
    if (this.selected) {
      this._select()
    }
  },
  beforeDestroy() {
    // It could be that the cell has already been unselected, in that case we don't
    // have to before unselect twice.
    if (this.selected) {
      this._beforeUnSelect()
    }
  },
  methods: {
    /**
     * Adds all the event listeners related to all the field types, for example when a
     * user presses the one of the arrow keys, tab, backspace, double clicks etc. This
     * method is not meant to be overwritten.
     */
    _select() {
      this.$el.clickEvent = (event) => {
        const timestamp = new Date().getTime()

        if (
          this.clickTimestamp !== null &&
          timestamp - this.clickTimestamp < 200
        ) {
          this.doubleClick(event)
        }

        this.clickTimestamp = timestamp
      }
      this.$el.addEventListener('click', this.$el.clickEvent)

      // Register a body click event listener so that we can detect if a user has
      // clicked outside the field. If that happens we want to unselect the field and
      // possibly save the value.
      this.$el.clickOutsideEventCancel = onClickOutside(
        this.$el,
        (target, event) => {
          if (
            // Check if the event has the 'preventFieldCellUnselect' attribute which
            // if true should prevent the field from being unselected.
            !(
              'preventFieldCellUnselect' in event &&
              event.preventFieldCellUnselect
            ) &&
            // If the child field allows to unselect when clicked outside.
            this.canUnselectByClickingOutside(event)
          ) {
            this.$emit('unselect')
          }
        }
      )

      // Event that is called when a key is pressed while the field is selected.
      this.$el.keyDownEvent = (event) => {
        // When for example a related modal is open all the key combinations must be
        // ignored because the focus is not in the cell.
        if (!this.canKeyDown(event)) {
          return
        }

        // If the tab or arrow keys are pressed we want to select the next field. This
        // is however out of the scope of this component so we emit the selectNext
        // event that the GridView can handle.
        const { key, shiftKey } = event
        const arrowKeysMapping = {
          ArrowLeft: 'selectPrevious',
          ArrowUp: 'selectAbove',
          ArrowRight: 'selectNext',
          ArrowDown: 'selectBelow',
        }
        if (this.canSelectNext(event)) {
          if (Object.keys(arrowKeysMapping).includes(key)) {
            event.preventDefault()
            this.$emit(arrowKeysMapping[key])
          } else if (key === 'Tab') {
            event.preventDefault()
            this.$emit(shiftKey ? 'selectPrevious' : 'selectNext')
          } else if (key === 'Enter' && shiftKey) {
            event.preventDefault()
            this.$emit('selectBelow')
          }
        }

        // Removes the value if the backspace/delete key is pressed.
        if ((key === 'Delete' || key === 'Backspace') && this.canEmpty(event)) {
          event.preventDefault()
          const value = this.$registry
            .get('field', this.field.type)
            .getEmptyValue(this.field)
          const oldValue = this.value
          if (
            value !== oldValue &&
            !this.readOnly &&
            !this.field._.type.isReadOnly
          ) {
            this.$emit('update', value, oldValue)
          }
        }
      }
      document.body.addEventListener('keydown', this.$el.keyDownEvent)

      this.$el.copyEventListener = (event) => {
        if (!this.canKeyDown(event) || !this.canCopy(event)) return

        this.copySelectionToClipboard(
          [this.field],
          [{ [`field_${this.field.id}`]: this.value }]
        )
      }
      document.addEventListener('copy', this.$el.copyEventListener)

      // Updates the value of the field when a user pastes something in the field.
      this.$el.pasteEventListener = async (event) => {
        if (!this.canPaste(event)) {
          return
        }

        // Try to call the field handler if one exists
        if (this.onPaste) {
          // If the return value of onPaste is true then we must stop event handling
          // here. It means the event has already been handled.
          if (this.onPaste(event)) {
            return
          }
        }

        try {
          const [data, jsonData] = await this.extractClipboardData(event)
          // A grid field cell can only handle one single value. We try to extract
          // that from the clipboard and update the cell, otherwise we emit the
          // paste event up.
          if (data.length === 1 && data[0].length === 1) {
            const value = this.$registry
              .get('field', this.field.type)
              .prepareValueForPaste(
                this.field,
                data[0][0],
                jsonData !== null ? jsonData[0][0] : undefined
              )
            const oldValue = this.value

            if (
              value !== undefined &&
              value !== oldValue &&
              !this.readOnly &&
              !this.field._.type.isReadOnly
            ) {
              this.$emit('update', value, oldValue)
            }
          } else {
            // This is a multi cell paste
            event.stopPropagation()
            this.$emit('paste', { textData: data, jsonData })
          }
        } catch (e) {}
      }
      document.addEventListener('paste', this.$el.pasteEventListener)

      this.clickTimestamp = new Date().getTime()
      this.select()

      // Emit the selected event so that the parent component can take an action like
      // making sure that the element fits in the viewport.
      this.$emit('selected', { component: this })
    },
    /**
     * Removes all the listeners related to all field types.
     */
    _beforeUnSelect() {
      this.$el.removeEventListener('click', this.$el.clickEvent)
      if (
        Object.prototype.hasOwnProperty.call(
          this.$el,
          'clickOutsideEventCancel'
        )
      ) {
        this.$el.clickOutsideEventCancel()
      }
      document.body.removeEventListener('keydown', this.$el.keyDownEvent)
      document.removeEventListener('copy', this.$el.copyEventListener)
      document.removeEventListener('paste', this.$el.pasteEventListener)
      this.beforeUnSelect()
      this.$emit('unselected', {})
    },
    /**
     * Method that is called when the column is selected. For example when clicked
     * on the field. This is the moment to register event listeners if they are needed.
     */
    select() {},
    /**
     * Method that is called when the column is unselected. For example when clicked
     * outside the field. This is the moment to remove any event listeners.
     */
    beforeUnSelect() {},
    /**
     * Method that is called when the column is double clicked. Some grid fields want
     * to do something here apart from triggering the selected state. A boolean
     * toggles its value for example.
     */
    doubleClick() {},
    /**
     * There are keyboard shortcuts to select the next or previous field. For
     * example when the arrow or tab keys are pressed. The GridViewField component
     * first asks if this is allowed by calling this function. If false is returned
     * the next field is not going to be selected.
     */
    canSelectNext() {
      return true
    },
    /**
     * If the user presses ctrl/cmd + c while a field is selected, the value is
     * going to be copied to the clipboard. In some cases, for example when the user
     * is editing the value, we do not want to copy the value. If false is returned
     * the value won't be copied.
     */
    canCopy() {
      return true
    },
    /**
     * If the user presses ctrl/cmd + v while a field is selected, the value is
     * overwritten with the data of the clipboard. In some cases, for example when the
     * user is editing the value, we do not want to change the value. If false is
     * returned the value won't be changed.
     */
    canPaste() {
      return true
    },
    /**
     * If the user presses delete or backspace while a field is selected, the value is
     * deleted. In some cases, for example when the user is editing the value, we do
     * not want to delete the value. If false is returned the value won't be changed.
     */
    canEmpty() {
      return true
    },
    /**
     * If the user clicks outside the cell, the cell is automatically unselected. In
     * some cases, for example when you have a context menu as helper, you might not
     * want to unselect when the user clicks in the context menu. The can be
     * prevented by returned false here. The context menu lives at the root of the
     * body element and not inside the cell.
     */
    canUnselectByClickingOutside() {
      return true
    },
    /**
     * It must be possible for a field to ignore all key combinations. For example when
     * it is possible for a field to open a modal to select some data, the
     * backspace/delete key should not empty the field at that moment.
     */
    canKeyDown() {
      return true
    },
  },
}
