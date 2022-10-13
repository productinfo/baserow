import faker

from .sso import SamlFixture


class EnterpriseFixtures(SamlFixture):
    faker = faker.Faker()
