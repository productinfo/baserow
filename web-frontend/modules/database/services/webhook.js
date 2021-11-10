export default (client) => {
  return {
    fetchAll(tableId) {
      return client.get(`/database/tables/${tableId}/webhooks/`)
    },
    create(tableId, values) {
      return client.post(`/database/tables/${tableId}/webhooks/`, values)
    },
    get(tableId, webhookId) {
      return client.get(`/database/tables/${tableId}/webhooks/${webhookId}/`)
    },
    update(tableId, webhookId, values) {
      return client.patch(
        `/database/tables/${tableId}/webhooks/${webhookId}/`,
        values
      )
    },
    delete(tableId, webhookId) {
      return client.delete(`/database/tables/${tableId}/webhooks/${webhookId}/`)
    },
    call(tableId, values) {
      return client.post(`/database/tables/${tableId}/webhooks/call/`, values)
    },
  }
}