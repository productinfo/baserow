export default {
  methods: {
    getCollaboratorName(collaboratorValue, store) {
      if (store === undefined) {
        store = this.$store
      }

      const user = store.getters['group/getUserById'](collaboratorValue.id)
      if (user) {
        return "store " + user.name
      } else {
        return "api " + collaboratorValue.name
      }
    },
    getCollaboratorNameInitials(collaboratorValue, store) {
      return this.getCollaboratorName(collaboratorValue, store).slice(0, 1).toUpperCase()
    },
  },
}
