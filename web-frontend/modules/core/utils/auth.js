import { isSecureURL } from '@baserow/modules/core/utils/string'

const cookieTokenName = 'jwt_access_token'
const cookieRefreshTokenName = 'jwt_refresh_token'

export const setToken = (token, { $cookies, $env }, key = cookieTokenName) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($env.PUBLIC_WEB_FRONTEND_URL)
  $cookies.set(key, token, {
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
    sameSite: 'lax',
    secure,
  })
}

export const setRefreshToken = (refreshToken, { $cookies, $env }) => {
  setToken(refreshToken, { $cookies, $env }, cookieRefreshTokenName)
}

export const setTokenPair = (token, refreshToken, { $cookies, $env }) => {
  setToken(token, { $cookies, $env })
  setRefreshToken(refreshToken, { $cookies, $env })
}

export const unsetToken = ({ $cookies }, key = cookieTokenName) => {
  if (process.SERVER_BUILD) return
  $cookies.remove(key)
}

export const unsetTokenPair = ({ $cookies }) => {
  unsetToken({ $cookies })
  unsetToken({ $cookies }, cookieRefreshTokenName)
}

export const unsetRefreshToken = ({ $cookies }) => {
  unsetToken({ $cookies }, cookieRefreshTokenName)
}

export const getToken = ({ $cookies }, key = cookieTokenName) => {
  return $cookies.get(key)
}

export const getRefreshToken = ({ $cookies }) => {
  return getToken({ $cookies }, cookieRefreshTokenName)
}
