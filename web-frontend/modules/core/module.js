import path from 'path'
import _ from 'lodash'
import serveStatic from 'serve-static'

import { routes } from './routes'
import head from './head'

export default function DatabaseModule(options) {
  /**
   * This function adds a plugin, but rather then prepending it to the list it will
   * be appended.
   */
  this.appendPlugin = template => {
    this.addPlugin(template)
    this.options.plugins.push(this.options.plugins.splice(0, 1)[0])
  }

  // Baserow must be run in universal mode.
  this.options.mode = 'universal'

  // Set the default head object, but override the configured head.
  // @TODO if a child is a list the new children must be appended instead of overriden.
  this.options.head = _.merge({}, head, this.options.head)

  // Store must be true in order for the store to be injected into the context.
  this.options.store = true

  // Register new alias to the web-frontend directory.
  this.options.alias['@baserow'] = path.resolve(__dirname, '../../')

  // The core depends on these modules.
  this.requireModule('@nuxtjs/axios')
  this.requireModule('cookie-universal-nuxt')

  // Serve the static directory
  // @TODO we might need to change some things here for production. (See:
  //  https://github.com/nuxt/nuxt.js/blob/5a6cde3ebc23f04e89c30a4196a9b7d116b6d675/
  //  packages/server/src/server.js)
  const staticMiddleware = serveStatic(
    path.resolve(__dirname, 'static'),
    this.options.render.static
  )
  this.addServerMiddleware(staticMiddleware)

  // Add the layouts
  this.addLayout(path.resolve(__dirname, 'layouts/app.vue'), 'app')
  this.addLayout(path.resolve(__dirname, 'layouts/login.vue'), 'login')

  const plugins = [
    'middleware.js',
    'plugin.js',
    'plugins/auth.js',
    'plugins/clientHandler.js',
    'plugins/global.js',
    'plugins/vuelidate.js'
  ]
  plugins.forEach(plugin => {
    this.addPlugin({
      src: path.resolve(__dirname, plugin)
    })
  })

  this.extendRoutes(configRoutes => {
    // Remove all the routes created by nuxt.
    let i = configRoutes.length
    while (i--) {
      if (configRoutes[i].component.indexOf('/@nuxt/') !== -1) {
        configRoutes.splice(i, 1)
      }
    }

    // Add the routes from the ./routes.js.
    configRoutes.push(...routes)
  })

  // Add a default authentication middleware. In order to add a new middleware the
  // middleware.js file has to be changed.
  this.options.router.middleware.push('authentication')

  // Add the main scss file which contains all the generic scss code.
  this.options.css.push(path.resolve(__dirname, 'assets/scss/default.scss'))
}
