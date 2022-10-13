from django.apps import AppConfig
from django.db.models.signals import post_migrate


class BaserowEnterpriseConfig(AppConfig):
    name = "baserow_enterprise"

    def ready(self):
        from baserow_enterprise.api.member_data_types import (
            EnterpriseMemberTeamsDataType,
        )
        from baserow_enterprise.role.actions import AssignRoleActionType
        from baserow_enterprise.teams.actions import (
            CreateTeamActionType,
            CreateTeamSubjectActionType,
            DeleteTeamActionType,
            DeleteTeamSubjectActionType,
            UpdateTeamActionType,
        )
        from baserow_enterprise.trash_types import TeamTrashableItemType

        from baserow.api.user.registries import member_data_registry
        from baserow.core.action.registries import action_type_registry
        from baserow.core.registries import plugin_registry
        from baserow.core.trash.registries import trash_item_type_registry

        from .plugins import EnterprisePlugin

        plugin_registry.register(EnterprisePlugin())

        action_type_registry.register(CreateTeamActionType())
        action_type_registry.register(UpdateTeamActionType())
        action_type_registry.register(DeleteTeamActionType())
        action_type_registry.register(CreateTeamSubjectActionType())
        action_type_registry.register(DeleteTeamSubjectActionType())
        action_type_registry.register(AssignRoleActionType())

        trash_item_type_registry.register(TeamTrashableItemType())

        member_data_registry.register(EnterpriseMemberTeamsDataType())

        from baserow.core.registries import permission_manager_type_registry

        from .role.permission_manager import RolePermissionManagerType

        permission_manager_type_registry.register(RolePermissionManagerType())

        from baserow.core.registries import operation_type_registry
        from .role.operations import AssignRoleGroupOperationType

        operation_type_registry.register(AssignRoleGroupOperationType())

        # Create default roles
        post_migrate.connect(sync_default_roles_after_migrate, sender=self)


def sync_default_roles_after_migrate(sender, **kwargs):
    from .role.default_roles import default_roles

    apps = kwargs.get("apps", None)

    if apps is not None:

        try:
            Operation = apps.get_model("core", "Operation")
            Role = apps.get_model("baserow_enterprise", "Role")
        except (LookupError):
            print("Skipping role creation as related models does not exist.")
        else:
            for role_name, operations in default_roles.items():
                role, _ = Role.objects.update_or_create(
                    uid=role_name,
                    defaults={"name": f"role.{role_name}", "default": True},
                )
                role.operations.all().delete()

                for operation_type in operations:
                    operation, _ = Operation.objects.get_or_create(
                        name=operation_type.type
                    )
                    role.operations.add(operation)
