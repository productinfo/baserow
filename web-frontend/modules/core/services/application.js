export default (client) => {
  return {
    fetch(applicationId) {
      return client.get(`/applications/${applicationId}/`)
    },
    fetchAll(groupId = null) {
      const groupUrl = groupId !== null ? `group/${groupId}/` : ''
      return client.get(`/applications/${groupUrl}`)
    },
    create(groupId, values) {
      return client.post(`/applications/group/${groupId}/`, values)
    },
    asyncDuplicate(applicationId) {
      return client.post(`/applications/${applicationId}/async_duplicate/`)
    },
    get(applicationId) {
      return client.get(`/applications/${applicationId}/`)
    },
    update(applicationId, values) {
      return client.patch(`/applications/${applicationId}/`, values)
    },
    order(groupId, order) {
      return client.post(`/applications/group/${groupId}/order/`, {
        application_ids: order,
      })
    },
    delete(applicationId) {
      return client.delete(`/applications/${applicationId}/`)
    },
  }
}
