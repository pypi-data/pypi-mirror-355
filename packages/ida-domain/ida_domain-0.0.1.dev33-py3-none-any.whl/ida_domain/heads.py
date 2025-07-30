from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import ida_bytes
import ida_ida
import ida_idaapi
import idadex
import idc

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from .database import Database

logger = logging.getLogger(__name__)


@decorate_all_methods(check_db_open)
class Heads:
    """
    Provides access to heads(instructions or data items) in the IDA database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a heads handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_all(self):
        """
        Retrieves an iterator over all heads in the database.

        Returns:
            An iterator over the heads.
        """
        return self.get_between(ida_ida.inf_get_min_ea(), ida_ida.inf_get_max_ea())

    def get_between(self, start: idadex.ea_t, end: idadex.ea_t):
        """
        Retrieves all basic heads between two addresses.

        Args:
            start_ea: Start address of the range.
            end_ea: End address of the range.

        Returns:
            An iterator over the heads.
        """
        ea = start
        if not idc.is_head(ida_bytes.get_flags(ea)):
            ea = ida_bytes.next_head(ea, end)
        while ea < end and ea != ida_idaapi.BADADDR:
            yield ea
            ea = ida_bytes.next_head(ea, end)

    def get_next(self, ea: idadex.ea_t) -> idadex.ea_t | None:
        """
        Retrieves the next head.

        Args:
            ea: Current head address.

        Returns:
            Next head, on error returns None.
        """
        ea = ida_bytes.next_head(ea, ida_ida.inf_get_max_ea())
        return ea if ea != ida_idaapi.BADADDR else None

    def get_prev(self, ea: idadex.ea_t) -> idadex.ea_t | None:
        """
        Retrieves the prev head.

        Args:
            ea: Current head address.

        Returns:
            Prev head, on error returns None.
        """
        ea = ida_bytes.prev_head(ea, ida_ida.inf_get_min_ea())
        return ea if ea != ida_idaapi.BADADDR else None
