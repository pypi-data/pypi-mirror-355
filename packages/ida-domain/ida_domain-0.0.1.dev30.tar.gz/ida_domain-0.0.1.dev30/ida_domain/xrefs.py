from __future__ import annotations

from typing import TYPE_CHECKING

import ida_xref

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from .database import Database


@decorate_all_methods(check_db_open)
class Xrefs:
    """
    Provides access to cross-reference (xref) analysis in the IDA database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a xrefs handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_to(self, ea: int):
        """
        Creates an iterator over all xrefs pointing to a given address.

        Args:
            ea: Target effective address.

        Returns:
            An iterator over incoming xrefs.
        """
        xref = ida_xref.xrefblk_t()
        success = xref.first_to(ea, ida_xref.XREF_ALL)

        while success:
            yield xref
            success = xref.next_to()

    def get_from(self, ea: int):
        """
        Creates an iterator over all xrefs originating from a given address.

        Args:
            ea: Source effective address.

        Returns:
            An iterator over outgoing xrefs.
        """
        xref = ida_xref.xrefblk_t()
        success = xref.first_from(ea, ida_xref.XREF_ALL)

        while success:
            yield xref
            success = xref.next_from()
