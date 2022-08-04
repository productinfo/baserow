from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from baserow.core.exceptions import TrashItemDoesNotExist
from baserow.core.registry import (
    Instance,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)


class TrashableItemType(ModelInstanceMixin, Instance, ABC):
    """
    A TrashableItemType specifies a baserow model which can be trashed.
    """

    def lookup_trashed_item(
        self, trashed_entry, trash_item_lookup_cache: Dict[str, Any] = None
    ):
        """
        Returns the actual instance of the trashed item. By default simply does a get
        on the model_class's trash manager.

        :param trash_item_lookup_cache: A dictionary which can be used to store
            expensive objects used to lookup this item which could be re-used when
            looking up other items of this type.
        :param trashed_entry: The entry to get the real trashed instance for.
        :return: An instance of the model_class with trashed_item_id
        """

        try:
            return self.model_class.trash.get(id=trashed_entry.trash_item_id)
        except self.model_class.DoesNotExist:
            raise TrashItemDoesNotExist()

    @abstractmethod
    def permanently_delete_item(
        self,
        trashed_item: Any,
        trash_item_lookup_cache: Dict[str, Any] = None,
    ):
        """
        Should be implemented to actually delete the specified trashed item from the
        database and do any other required clean-up.

        :param trashed_item: The item to delete permanently.
        :param trash_item_lookup_cache: If a cache is being used to speed up trash
            item lookups it should be provided here so trash items can invalidate the
            cache if when they are deleted a potentially cache item becomes invalid.
        """

        pass

    @property
    def requires_parent_id(self) -> bool:
        """
        :returns True if this trash type requires a parent id to lookup a specific item,
            false if only the trash_item_id is required to perform a lookup.
        """

        return False

    @abstractmethod
    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        """
        Returns the parent for this item.

        :param trashed_item: The item to lookup a parent for.
        :returns Either the parent item or None if this item has no parent.
        """

        pass

    @abstractmethod
    def restore(self, trashed_item: Any, trash_entry):
        """
        Called when a trashed item should be restored. Will set trashed to true and
        save. Should be overridden if additional actions such as restoring related
        items or web socket signals are needed.

        :param trash_entry: The trash entry that was restored from.
        :param trashed_item: The item that to be restored.
        """

        trashed_item.trashed = False
        trashed_item.save()

    @abstractmethod
    def get_name(self, trashed_item: Any) -> str:
        """
        Should return the name of this particular trashed item to display in the trash
        modal.

        :param trashed_item: The item to be named.
        :return The name of the trashed_item
        """

        pass

    def get_names(self, trashed_item: Any) -> str:
        """
        Should return an array of names of this particular trashed item to display in
        the trash modal. This is typically used when multiple items have been deleted
        in batch and can be visualized differently by the client.

        :param trashed_item: The item to be named.
        :return The names of the trashed_item.
        """

        pass

    def trash(self, item_to_trash, requesting_user):
        """
        Saves trashed=True on the provided item and should be overridden to perform any
        other cleanup and trashing other items related to item_to_trash.

        :return  An iterable of trashable model instances.
        """

        item_to_trash.trashed = True
        item_to_trash.save()

    def handle_perm_delete_out_of_shared_memory(self, failed_trash_item, exception):
        """
        Called when the trash_item failed to be perm deleted as the transaction tried
        to lock too many separate things in postgres, resulting in an out of shared
        memory exception.

        This method will not be called in any sort of atomic transaction giving
        you full control of how to use transactions in a way which prevents locking
        too many things.

        Use this method to run any steps that you can do to ensure
        the next time the perm delete is called it will succeed and not run out of
        locks, for example by perm deleting some items in their own transactions now so
        the job has less to delete later. If there is nothing safe and reasonable
        you can do, then just re-raise the exception.

        :param failed_trash_item: The trash item which failed to be perm deleted.
        :param exception: The specific exception that resulted from the failure.
        """

        raise exception


class TrashableItemTypeRegistry(ModelRegistryMixin, Registry):
    """
    The TrashableItemTypeRegistry contains models which can be "trashed" in baserow.
    When an instance of a trashable model is trashed it is removed from baserow but
    not permanently. Once trashed an item can then be restored to add it back to
    baserow just as it was when it was trashed.
    """

    name = "trashable"


trash_item_type_registry = TrashableItemTypeRegistry()
