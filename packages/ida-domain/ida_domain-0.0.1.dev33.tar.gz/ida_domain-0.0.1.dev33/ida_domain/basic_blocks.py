from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import ida_gdl

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from ida_funcs import func_t
    from ida_gdl import qbasic_block_t
    from idadex import ea_t

    from .database import Database


logger = logging.getLogger(__name__)


class _FlowChart(ida_gdl.FlowChart):
    """
    Flowchart class used to determine basic blocks.
    """

    def __init__(self, f=None, bounds=None, flags=0):
        super().__init__(f, bounds, flags)

    def _getitem(self, index):
        return self._q[index]


@decorate_all_methods(check_db_open)
class BasicBlocks:
    """
    Interface for working with basic blocks in functions.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a basic block handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_instructions(self, block: 'qbasic_block_t'):
        """
        Retrieves the instructions within a given basic block.

        Args:
            block: The basic block.

        Returns:
            An instruction iterator for the block.
        """
        if block is None or not hasattr(block, 'start_ea') or not hasattr(block, 'end_ea'):
            # Return empty iterator
            return self.m_database.instructions.get_between(0, 0)

        return self.m_database.instructions.get_between(block.start_ea, block.end_ea)

    def get_from_function(self, func: 'func_t', flags=0):
        """
        Retrieves the basic blocks within a given function.

        Args:
            func: The function to retrieve basic blocks from.
            flags: Optional qflow_chart_t flags.

        Returns:
            An iterable flowchart containing the basic blocks.
        """
        return _FlowChart(func, None, flags)

    def get_between(self, start: 'ea_t', end: 'ea_t', flags=0):
        """
        Retrieves the basic blocks within a given range.

        Args:
            start: The start address to retrieve basic blocks from.
            end: The end address to retrieve basic blocks from.
            flags: Optional qflow_chart_t flags.

        Returns:
            An iterable flowchart containing the basic blocks.
        """
        return _FlowChart(None, (start, end), flags)
