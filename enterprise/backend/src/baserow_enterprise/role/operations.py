from baserow.core.registries import OperationType


class AssignRoleGroupOperationType(OperationType):
    type = "user.assign_role"
    context_scope_name = "group"
