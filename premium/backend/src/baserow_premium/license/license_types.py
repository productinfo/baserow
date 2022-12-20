from baserow_premium.license.features import PREMIUM
from baserow_premium.license.models import License, LicenseUser
from baserow_premium.license.registries import LicenseType, SeatUsageSummary


class PremiumLicenseType(LicenseType):
    type = "premium"
    order = 10
    features = [PREMIUM]

    def get_seat_usage_summary(self, obj: License) -> SeatUsageSummary:
        seats_taken = (
            obj.seats_taken if hasattr(obj, "seats_taken") else obj.users.all().count()
        )
        return SeatUsageSummary(
            seats_taken=seats_taken,
            free_users_count=0,
            num_users_with_highest_role={},
        )

    def handle_seat_overflow(self, seats_taken: int, license_object: License):
        # If there are more seats taken than the license allows, we need to
        # remove the active seats that are outside the limit.
        LicenseUser.objects.filter(
            pk__in=license_object.users.all()
            .order_by("pk")
            .values_list("pk")[license_object.seats : seats_taken]
        ).delete()
