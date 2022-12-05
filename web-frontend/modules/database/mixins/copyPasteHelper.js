/**
 * A mixin that can be used to copy and paste row values.
 */

import {
  getRichClipboard,
  setRichClipboard,
} from '@baserow/modules/database/utils/clipboard'

export default {
  methods: {
    copySelectionToClipboard(fields, rows) {
      const textData = []
      const jsonData = []
      for (const row of rows) {
        const text = fields.map((field) =>
          this.$registry
            .get('field', field.type)
            .prepareValueForCopy(field, row['field_' + field.id])
        )
        const json = fields.map((field) =>
          this.$registry
            .get('field', field.type)
            .prepareRichValueForCopy(field, row['field_' + field.id])
        )
        textData.push(text)
        jsonData.push(json)
      }
      const tsv = this.$papa.unparse(textData, {
        delimiter: '\t',
      })
      setRichClipboard(tsv, jsonData)
    },
    async extractClipboardData(event) {
      const { textRawData, jsonRawData } = getRichClipboard(event)
      const { data: textData } = await this.$papa.parsePromise(textRawData, {
        delimiter: '\t',
      })

      let jsonData = jsonRawData
      if (jsonData) {
        try {
          // Check if we have an array of arrays with At least one row with at least
          // one row with a value Otherwise the paste is empty
          if (
            Array.isArray(jsonRawData) &&
            jsonRawData.length === textData.length &&
            jsonRawData.every((row) => Array.isArray(row)) &&
            jsonRawData.some((row) => row.length > 0)
          ) {
            jsonData = JSON.parse(jsonRawData)
          }
        } catch (e) {}
      }

      return [textData, jsonData]
    },
  },
}
