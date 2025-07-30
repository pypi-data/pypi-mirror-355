from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import ida_idaapi
import ida_name

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from idadex import ea_t

    from .database import Database


@decorate_all_methods(check_db_open)
class Names:
    """
    Provides access to symbol and label management in the IDA database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a names handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_count(self) -> int:
        """
        Retrieves the total number of named elements in the database.

        Returns:
            The number of named elements.
        """
        return ida_name.get_nlist_size()

    def get_at_index(self, index: int) -> Tuple['ea_t', str]:
        """
        Retrieves the named element at the specified index.

        Returns
          A Tuple (effective address, name) at the given index.
        """
        if index < ida_name.get_nlist_size():
            return ida_name.get_nlist_ea(index), ida_name.get_nlist_name(index)
        return ida_idaapi.BADADDR, ''

    def get_at(self, ea: 'ea_t') -> str | None:
        """
        Retrieves the name at the specified address.

        Returns
            A Tuple (bool success, name string). If the name doesn't exist, bool is false.
        """
        return ida_name.get_name(ea)

    def get_all(self):
        """
        Returns an iterator over all named elements in the database.

        Returns:
            A names iterator.
        """
        index = 0
        while index < ida_name.get_nlist_size():
            yield ida_name.get_nlist_ea(index), ida_name.get_nlist_name(index)
            index += 1
