import logging

from users.models import OpenTAUser

from .abstract_entity_factory import AbstractEntityFactory

logger = logging.getLogger(__name__)


class OpenTAUserFactory(AbstractEntityFactory[OpenTAUser]):
    """An object used in test suites used to create one or more OpenTA Users.

    The model objects contain fake data that is populated using Faker.

    """

    def build(self, **kwargs: str) -> OpenTAUser:
        defaults = {"user": None, **kwargs}
        openta_user: OpenTAUser = OpenTAUser(**defaults)
        self._default = openta_user
        return openta_user

    def create(self, **kwargs: str) -> OpenTAUser:
        openta_user = self.build(**kwargs)
        openta_user.save()
        return openta_user
