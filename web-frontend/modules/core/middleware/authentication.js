import { getToken, setToken } from '@baserow/modules/core/utils/auth'

export default function ({ store, req, app, route }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // If a token is present in the query string, replace the cookie with it and start using it.
  // This is the case for SSO logins.
  let refreshToken = route.query.token
  if (refreshToken) {
    setToken(route.query.token, app)
  } else {
    refreshToken = getToken(app)
  }

  // If there already is a token we will refresh it to check if it is valid and
  // to get fresh user information. This will probably happen on the server
  // side.
  if (refreshToken && !store.getters['auth/isAuthenticated']) {
    return store.dispatch('auth/refresh', refreshToken)
  }
}
