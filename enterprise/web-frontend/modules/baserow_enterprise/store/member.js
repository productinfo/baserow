/**
 * This store serves the purpose of keeping track of members. A member is a user with
 * a role_assigment, meaning that they have a certain role in a certain scope.
 * A scope could be a database, or a table for example.
 */

// TODO remove
const mockDataMembers = [
  {
    user: {
      id: 1,
      name: 'alex',
      email: 'alex@baserow.io',
    },
    role_assignments: [
      {
        role: 'BUILDER',
        scope: 35,
        scope_type: 'database',
      },
    ],
  },
  {
    user: {
      id: 2,
      name: 'james',
      email: 'james@baserow.io',
    },
    role_assignments: [
      {
        role: 'BUILDER',
        scope: 35,
        scope_type: 'database',
      },
    ],
  },
]

export const state = () => ({
  members: [],
})

export const mutations = {
  SET_MEMBERS(state, members) {
    state.members = members
  },
  ADD_MEMBER(sate, member) {
    state.members.push(member)
  },
  UPDATE_MEMBER(state, { userId, values }) {
    const index = state.members.findIndex((member) => member.user.id === userId)
    if (index !== -1) {
      Object.assign(state.members[index], state.members[index], values)
    }
  },
}
export const actions = {
  addMember({ commit }, member) {
    // TODO add actual api request

    commit('ADD_MEMBER', member)
  },
  updateMember({ commit }, { userId, values }) {
    // TODO add actual api request

    commit('UPDATE_MEMBER', { userId, values })
  },
  fetchMembers({ commit }) {
    // TODO add actual api request
    commit('SET_MEMBERS', mockDataMembers)
  },
}
export const getters = {
  getMembers(state) {
    return state.members
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
