def has_active_enterprise_license():
    return True


def check_active_enterprise_license(user):
    return True


class NoEnterpriseLicenseError(Exception):
    pass
