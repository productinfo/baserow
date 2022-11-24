export default (client, $hasFeature) => {
  return {
    // TODO implement once endpoint exists
    get(group) {
      if ($hasFeature('RBAC', group.id)) {
        return {
          data: [
            { uid: 'ADMIN' },
            { uid: 'BUILDER' },
            { uid: 'EDITOR' },
            { uid: 'COMMENTER' },
            { uid: 'VIEWER' },
            { uid: 'NO_ACCESS' },
            { uid: 'NO_ROLE_LOW_PRIORITY', allowed_scope_types: ['group'] },
          ],
        }
      }
      return {
        data: [{ uid: 'ADMIN' }, { uid: 'MEMBER' }],
      }
    },
  }
}
