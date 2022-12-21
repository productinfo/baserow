from typing import List

from baserow.api.user.registries import UserDataType
from baserow.core.handler import CoreHandler


class GlobalPermissionsDataType(UserDataType):
    type = "permissions"

    def get_user_data(self, user, request) -> List[dict]:
        """
        Responsible for annotating `User` responses with global permissions
        (which don't relate to a `Group`).
        """

        permissions = []
        manager_types_to_expose = ["core", "staff", "setting_operation"]
        global_permissions = CoreHandler().get_permissions(user)
        for global_permission in global_permissions:
            name = global_permission["name"]
            if name in manager_types_to_expose:
                operations = global_permission["permissions"]
                if type(operations) == dict:
                    for perm_key, perm_val in global_permission["permissions"].items():
                        if type(perm_val) == list:
                            operations = perm_val
                            break
                permissions.append({"name": name, "permissions": operations})

        return permissions
