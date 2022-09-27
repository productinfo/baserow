from baserow.core.registry import Registry, Instance


class LicenseType(Instance):
    pass


class LicenseTypeRegistry(Registry[LicenseType]):
    type = "license_type"


license_type_registry: LicenseTypeRegistry = LicenseTypeRegistry()
