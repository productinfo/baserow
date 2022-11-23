class CantAssignRoleExceptionToAdmin(Exception):
    """
    Raised when the user try to assign a role to scope that has already the ADMIN
    computed role.
    """
