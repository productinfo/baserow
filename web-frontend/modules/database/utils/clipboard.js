/**
 * Copies the given text to the clipboard by temporarily creating a textarea and
 * using the documents `copy` command.
 */
export const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
}

const LOCAL_STORAGE_CLIPBOARD_KEY = 'baserow.clipboardData'

/**
 * Values should be an object with mimetypes as key and clipboard content for this type
 * as value. This allow add the same data with multiple representation to the clipboard.
 * We can have a row saved as tsv string or as json string. Values must be strings.
 * @param {object} values object of mimetypes -> clipboard content.
 */
export const setRichClipboard = (text, jsonData) => {
  copyToClipboard(text)
  localStorage.setItem(
    LOCAL_STORAGE_CLIPBOARD_KEY,
    JSON.stringify({ text, jsonData })
  )
}

export const getRichClipboard = (event) => {
  const textRawData = event.clipboardData.getData('text/plain')
  let jsonRawData

  let clipboardData = localStorage.getItem(LOCAL_STORAGE_CLIPBOARD_KEY)
  try {
    clipboardData = JSON.parse(clipboardData)
    if (clipboardData.text === textRawData) {
      jsonRawData = clipboardData.jsonData
    } else {
      throw new Error(
        'Clipboard data is not the same as the local storage data'
      )
    }
  } catch (e) {
    localStorage.removeItem(LOCAL_STORAGE_CLIPBOARD_KEY)
  }
  return { textRawData: textRawData.trim(), jsonRawData }
}
