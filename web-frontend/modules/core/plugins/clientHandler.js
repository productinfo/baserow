import { client } from '@baserow/modules/core/services/client'
import { lowerCaseFirst } from '@baserow/modules/core/utils/string'

export class ResponseErrorMessage {
  constructor(title, message) {
    this.title = title
    this.message = message
  }
}

class ErrorHandler {
  constructor(store, response, code = null, detail = null) {
    this.isHandled = false
    this.store = store
    this.response = response
    this.setError(code, detail)

    // A temporary global errorMap containing error messages for certain errors codes.
    // This must later be replaced by a more dynamic way.
    this.errorMap = {
      ERROR_USER_NOT_IN_GROUP: new ResponseErrorMessage(
        'Action not allowed.',
        "The action couldn't be completed because you aren't a " +
          'member of the related group.'
      ),
      // @TODO move these errors to the module.
      ERROR_TABLE_DOES_NOT_EXIST: new ResponseErrorMessage(
        "Table doesn't exist.",
        "The action couldn't be completed because the related table doesn't exist" +
          ' anymore.'
      ),
      ERROR_ROW_DOES_NOT_EXIST: new ResponseErrorMessage(
        "Row doesn't exist.",
        "The action couldn't be completed because the related row doesn't exist" +
          ' anymore.'
      )
    }

    // A temporary notFoundMap containing the error messages for when the
    // response contains a 404 error based on the provided context name. Note
    // that an entry is not found a default message will be generated.
    this.notFoundMap = {}
  }

  /**
   * Changes the error code and details.
   */
  setError(code, detail) {
    this.code = code
    this.detail = detail
  }

  /**
   * Returns true if there is a readable error.
   * @return {boolean}
   */
  hasError() {
    return this.response !== undefined && this.response.code !== null
  }

  /**
   * Returns true is the response status code is equal to not found (404).
   * @return {boolean}
   */
  isNotFound() {
    return this.response !== undefined && this.response.status === 404
  }

  /**
   * Return true if there is a network error.
   * @return {boolean}
   */
  hasNetworkError() {
    return this.response === undefined
  }

  /**
   * Finds a message in the global errors or in the provided specific error map.
   */
  getErrorMessage(specificErrorMap = null) {
    if (
      specificErrorMap !== null &&
      specificErrorMap.hasOwnProperty(this.code)
    ) {
      return specificErrorMap[this.code]
    }

    if (this.errorMap.hasOwnProperty(this.code)) {
      return this.errorMap[this.code]
    }

    return new ResponseErrorMessage(
      'Action not completed.',
      "The action couldn't be completed because an unknown error has" +
        ' occured.'
    )
  }

  /**
   * Finds a not found message for a given context.
   */
  getNotFoundMessage(name) {
    if (!this.notFoundMap.hasOwnProperty(name)) {
      return new ResponseErrorMessage(
        `${lowerCaseFirst(name)} not found.`,
        `The selected ${name.toLowerCase()} wasn't found, maybe it has already been deleted.`
      )
    }
    return this.notFoundMap[name]
  }

  /**
   * Returns a standard network error message. For example if the API server
   * could not be reached.
   */
  getNetworkErrorMessage() {
    return new ResponseErrorMessage(
      'Network error',
      'Could not connect to the API server.'
    )
  }

  /**
   * If there is an error or the requested detail is not found an error
   * message related to the problem is returned.
   */
  getMessage(name = null, specificErrorMap = null) {
    if (this.hasNetworkError()) {
      return this.getNetworkErrorMessage()
    }
    if (this.hasError()) {
      return this.getErrorMessage(specificErrorMap)
    }
    if (this.isNotFound()) {
      return this.getNotFoundMessage(name)
    }
    return null
  }

  /**
   * If there is an error or the requested detail is not found we will try to
   * get find an existing message of one is not provided and notify the user
   * about what went wrong. After that the error is marked as handled.
   */
  notifyIf(name = null, message = null) {
    if (
      !(this.hasError() || this.hasNetworkError() || this.isNotFound()) ||
      this.isHandled
    ) {
      return
    }

    if (message === null) {
      message = this.getMessage(name)
    }

    this.store.dispatch(
      'notification/error',
      {
        title: message.title,
        message: message.message
      },
      { root: true }
    )

    this.handled()
  }

  /**
   * Will mark the error as handled so that the same error message isn't shown
   * twice.
   */
  handled() {
    this.isHandled = true
  }
}

export default function({ store }) {
  // Create a request interceptor to add the authorization token to every
  // request if the user is authenticated.
  client.interceptors.request.use(config => {
    if (store.getters['auth/isAuthenticated']) {
      const token = store.getters['auth/token']
      config.headers.Authorization = `JWT ${token}`
    }
    return config
  })

  // Create a response interceptor to add more detail tot the error message
  // and to create a notification when there is a network error.
  client.interceptors.response.use(
    response => {
      return response
    },
    error => {
      error.handler = new ErrorHandler(store, error.response)

      // Add the error message in the response to the error object.
      if (
        error.response &&
        'error' in error.response.data &&
        'detail' in error.response.data
      ) {
        error.handler.setError(
          error.response.data.error,
          error.response.data.detail
        )
      }

      return Promise.reject(error)
    }
  )
}
