/**
 * Copies the given text to the clipboard by temporarily creating a textarea and
 * using the documents `copy` command.
 */
export const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
}

const isSafariBrowser = () =>
  /^((?!chrome|android).)*safari/i.test(navigator.userAgent)

/**
 * Values should be an object with mimetypes as key and clipboard content for this type
 * as value. This allow add the same data with multiple representation to the clipboard.
 * We can have a row saved as tsv string or as json string. Values must be strings.
 * @param {object} values object of mimetypes -> clipboard content.
 */
export const setRichClipboard = (values) => {
  // In recent versions of Safari, the execCommand doesn't work, so we need to use the
  // clipboard API.
  if (isSafariBrowser()) {
    navigator.clipboard.writeText(values['text/plain'])
    // since the clipboard API accept only a few types, we use the localStorage
    // to save the other data needed to paste this back in the correct format
    localStorage.setItem('baserow.clipboardData', JSON.stringify(values))
  } else {
    const listener = (e) => {
      Object.entries(values).forEach(([type, content]) => {
        e.clipboardData.setData(type, content)
      })
      e.preventDefault()
      e.stopPropagation()
    }
    document.addEventListener('copy', listener)
    document.execCommand('copy')
    document.removeEventListener('copy', listener)
  }
}

export const getRichClipboard = (event) => {
  const textRawData = event.clipboardData.getData('text/plain')
  let jsonRawData

  // In recent versions of Safari, the execCommand doesn't work, so we need to get
  // the metadata from the localStorage.
  if (isSafariBrowser()) {
    let clipboardData = localStorage.getItem('baserow.clipboardData')
    localStorage.removeItem('baserow.clipboardData')
    try {
      clipboardData = JSON.parse(clipboardData)
      if (clipboardData['text/plain'] === textRawData) {
        jsonRawData = clipboardData['application/json']
      }
    } catch (e) {}
  } else if (event.clipboardData.types.includes('application/json')) {
    jsonRawData = event.clipboardData.getData('application/json')
  }
  return { textRawData: textRawData.trim(), jsonRawData }
}
