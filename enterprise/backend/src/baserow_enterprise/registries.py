import abc

from django.core.exceptions import ImproperlyConfigured
from django.dispatch import receiver, Signal

from baserow.core.exceptions import (
    InstanceTypeAlreadyRegistered,
    InstanceTypeDoesNotExist,
)
from baserow.core.registries import Registry
from baserow.core.registry import Instance


class AuditLogType(abc.ABC, Instance):
    """
    The audit log type is used to define what type of action is being logged and how
    the data should be displayed and translated in the audit log.
    """

    signal: Signal

    def __init__(self):
        if not self.signal:
            raise ImproperlyConfigured("The signal of an AuditLogType must be set.")

    @abc.abstractmethod
    def receiver(self, sender, *args, **kwargs):
        """
        This method is used to connect the audit log type to the related signal. It
        should return a function that will be called when the signal is triggered.
        The function should accept the following arguments:

        :param sender: The sender of the signal.
        :param instance: The instance that is related to the signal.
        :param user: The user
        """

        pass

    @abc.abstractmethod
    def get_type_description(self, audit_log_entry) -> str:
        """
        This method is used to get the (translatable) description of the type. The
        description is used to display the type in the audit log. It returns a
        string.

        :param audit_log_entry: The audit log entry that is related to the
            event.
        """

        pass

    @abc.abstractmethod
    def get_event_description(self, audit_log_entry) -> str:
        """
        This method is used to get the (translatable) description of the event.
        The description is used to display the event in the audit log. It
        returns a string.

        :param audit_log_entry: The audit log entry that is related to the
            event.
        """

        pass


class AuditLogTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    pass


class AuditLogTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass


class AuditLogTypeRegistry(Registry[AuditLogType]):
    """
    Contains all the registered audit log types. The audit log types are used to
    define what type of action is being logged and how the data should be displayed
    and translated in the audit log.
    """

    name = "audit_log"

    does_not_exist_exception_class = AuditLogTypeDoesNotExist
    already_registered_exception_class = AuditLogTypeAlreadyRegistered

    def register(self, audit_log_type: AuditLogType):
        """
        Registers a new audit log type and connect the type to the related
        signal. The audit log type is used to define what type of action is
        being logged and how the data should be displayed and translated in the
        audit log.

        :param audit_log_type: The audit log type that should be registered.
        """

        super().register(audit_log_type)

        # register the signal receiver
        receiver(audit_log_type.signal)(audit_log_type.receiver)


audit_log_type_registry = AuditLogTypeRegistry()
