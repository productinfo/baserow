import { StoreItemLookupError } from '@baserow/modules/core/errors'
import TeamService from '@baserow_enterprise/services/team'
import { CORE_ACTION_SCOPES } from '@baserow/modules/core/utils/undoRedoConstants'

function populateteam(team) {
  team._ = { loading: false, selected: false }
  return team
}

export const state = () => ({
  loaded: false,
  loading: false,
  items: [],
  selected: {},
})

export const mutations = {
  SET_LOADED(state, loaded) {
    state.loaded = loaded
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_ITEMS(state, items) {
    // Set some default values that we might need later.
    state.items = items.map((item) => {
      item = populateteam(item)
      return item
    })
  },
  SET_ITEM_LOADING(state, { team, value }) {
    if (!Object.prototype.hasOwnProperty.call(team, '_')) {
      return
    }
    team._.loading = value
  },
  ADD_ITEM(state, item) {
    item = populateteam(item)
    state.items.push(item)
  },
  UPDATE_ITEM(state, { id, values }) {
    const index = state.items.findIndex((item) => item.id === id)
    Object.assign(state.items[index], state.items[index], values)
  },
  ORDER_ITEMS(state, order) {
    state.items.forEach((team) => {
      const index = order.findIndex((value) => value === team.id)
      team.order = index === -1 ? 0 : index + 1
    })
  },
  DELETE_ITEM(state, id) {
    const index = state.items.findIndex((item) => item.id === id)
    state.items.splice(index, 1)
  },
  SET_SELECTED(state, team) {
    Object.values(state.items).forEach((item) => {
      item._.selected = false
    })
    team._.selected = true
    state.selected = team
  },
  UNSELECT(state) {
    Object.values(state.items).forEach((item) => {
      item._.selected = false
    })
    state.selected = {}
  },
}

export const actions = {
  /**
   * If not already loading or loaded it will trigger the fetchAll action which
   * will load all the teams for the user.
   */
  async loadAll({ state, dispatch }) {
    if (!state.loaded && !state.loading) {
      await dispatch('fetchAll')
    }
  },
  /**
   * Clears all the selected teams. Can be used when logging off.
   */
  clearAll({ commit, dispatch }) {
    commit('SET_ITEMS', [])
    commit('UNSELECT')
    commit('SET_LOADED', false)
    return dispatch('application/clearAll', undefined, { root: true })
  },
  /**
   * Changes the loading state of a specific team.
   */
  setItemLoading({ commit }, { team, value }) {
    commit('SET_ITEM_LOADING', { team, value })
  },
  /**
   * Fetches all the teams of an authenticated user.
   */
  async fetchAll({ commit }) {
    commit('SET_LOADING', true)

    try {
      const { data } = await TeamService(this.$client).fetchAll()
      commit('SET_LOADED', true)
      commit('SET_ITEMS', data)
    } catch {
      commit('SET_ITEMS', [])
    }

    commit('SET_LOADING', false)
  },
  async create({ commit, dispatch }, { groupId, values }) {
    const { data } = await TeamService(this.$client).create(groupId, values)
    dispatch('forceCreate', data)
    return data
  },
  forceCreate({ commit }, values) {
    commit('ADD_ITEM', values)
  },
  async update({ commit, dispatch }, { team, values }) {
    const { data } = await TeamService(this.$client).update(team.id, values)
    // Create a dict with only the values we want to update.
    const update = Object.keys(values).reduce((result, key) => {
      result[key] = data[key]
      return result
    }, {})
    dispatch('forceUpdate', { team, values: update })
  },
  forceUpdate({ commit }, { team, values }) {
    commit('UPDATE_ITEM', { id: team.id, values })
  },
  forceOrder({ commit }, order) {
    commit('ORDER_ITEMS', order)
  },
  async delete({ commit, dispatch }, team) {
    try {
      await TeamService(this.$client).delete(team.id)
      await dispatch('forceDelete', team)
    } catch (error) {
      // If the team to delete wasn't found we can just delete it from the
      // state.
      if (error.response && error.response.status === 404) {
        await dispatch('forceDelete', team)
      } else {
        throw error
      }
    }
  },
  forceDelete({ commit }, job) {
    commit('DELETE_ITEM', job.id)
  },
}

export const getters = {
  isLoaded(state) {
    return state.loaded
  },
  isLoading(state) {
    return state.loading
  },
  get: (state) => (id) => {
    return state.items.find((item) => item.id === id)
  },
  getAll(state) {
    return state.items
  },
  getAllSorted(state) {
    return state.items.map((g) => g).sort((a, b) => a.order - b.order)
  },
  hasSelected(state) {
    return Object.prototype.hasOwnProperty.call(state.selected, 'id')
  },
  selectedId(state) {
    if (!Object.prototype.hasOwnProperty.call(state.selected, 'id')) {
      throw new Error('There is no selected team.')
    }

    return state.selected.id
  },
  selectedteam(state) {
    if (!Object.prototype.hasOwnProperty.call(state.selected, 'id')) {
      throw new Error('There is no selected team.')
    }

    return state.selected
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
