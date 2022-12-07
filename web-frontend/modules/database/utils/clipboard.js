/**
 * Copies the given text to the clipboard by temporarily creating a textarea and
 * using the documents `copy` command.
 */
export const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
}

export const LOCAL_STORAGE_CLIPBOARD_KEY = 'baserow.clipboardData'

/**
 * This method gets the text and json data from the clipboard and from the local
 * storage. This is needed because we need the original metadata to be able to
 * restore the original format, but the clipboard only allows to store plain
 * text, html or images related mime types.
 * @param {*} event
 * @returns {object} An object with the textRawData and jsonRawData. The
 * textRawData is the plain text that is stored in the clipboard. The
 * jsonRawData is the rich json object with all the metadata needed to restore
 * the original data in the correct rich format.
 */
export const getRichClipboard = async (event) => {
  let textRawData
  let jsonRawData

  if (typeof navigator.clipboard.readtText !== 'undefined') {
    textRawData = await navigator.clipboard.readText()
  } else {
    textRawData = event.clipboardData.getData('text/plain')
  }

  let clipboardData = localStorage.getItem(LOCAL_STORAGE_CLIPBOARD_KEY)
  try {
    clipboardData = JSON.parse(clipboardData)
    if (clipboardData.text === textRawData) {
      jsonRawData = clipboardData.json
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
