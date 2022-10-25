from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run oauth2"

    def handle(self, *args, **options):

        from baserow_enterprise.sso.oauth2.models import (
            GoogleAuthProviderModel,
            GitHubAuthProviderModel,
        )

        m = GoogleAuthProviderModel()
        m.name = "Google"
        m.client_id = (
            "301549728349-a6rg277tvpt8r0u3vqutn38ri25rfbo1.apps.googleusercontent.com"
        )
        m.secret = "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"
        m.save()

        m2 = GitHubAuthProviderModel()
        m2.name = "GitHub"
        m2.client_id = "3d8e919cb739d5203076"
        m2.secret = "be31a2fd16d5f239f0d6c0635942a50b183710ac"
        m2.save()
