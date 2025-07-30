from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import ida_bytes
import ida_idaapi
import ida_nalt
import ida_strlist

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from idadex import ea_t

    from .database import Database


@decorate_all_methods(check_db_open)
class Strings:
    """
    Provides access to string-related operations in the IDA database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a strings handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_count(self) -> int:
        """
        Retrieves the total number of extracted strings.

        Returns:
            The number of stored strings.
        """
        return ida_strlist.get_strlist_qty()

    def get_at_index(self, index: int) -> Tuple['ea_t', str]:
        """
        Retrieves the string at the specified index.

        Args:
            index: Index of the string to retrieve.

        Returns:
            A pair (effective address, string content) at the given index.
        """
        if index < ida_strlist.get_strlist_qty():
            si = ida_strlist.string_info_t()
            if ida_strlist.get_strlist_item(si, index):
                return si.ea, ida_bytes.get_strlit_contents(si.ea, -1, ida_nalt.STRTYPE_C).decode(
                    'utf-8'
                )
        return ida_idaapi.BADADDR, ''

    def get_at(self, ea: 'ea_t') -> str | None:
        """
        Retrieves the string located at the specified address.

        Args:
            ea: The effective address.

        Returns:
            A pair (success, string content). If not found, success is false.
        """
        ret = ida_bytes.get_strlit_contents(ea, -1, ida_nalt.STRTYPE_C)
        if ret is not None:
            return ret.decode('utf-8')
        return None

    def get_all(self):
        """
        Retrieves an iterator over all extracted strings in the database.

        Returns:
            A StringsIterator instance.
        """
        for current_index in range(0, ida_strlist.get_strlist_qty()):
            si = ida_strlist.string_info_t()
            if ida_strlist.get_strlist_item(si, current_index):
                yield (
                    si.ea,
                    ida_bytes.get_strlit_contents(si.ea, -1, ida_nalt.STRTYPE_C).decode('utf-8'),
                )
