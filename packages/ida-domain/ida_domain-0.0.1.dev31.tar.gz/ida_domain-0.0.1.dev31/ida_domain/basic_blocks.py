from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

import ida_gdl
import ida_kernwin

if TYPE_CHECKING:
    from ida_gdl import qbasic_block_t
    from idadex import ea_t

    from .database import Database


class BasicBlocks:
    """
    Interface for working with basic blocks in functions.
    """

    class Iterator:
        """Iterator for basic blocks in a function."""

        def __init__(self, database: 'Database', start_ea: 'ea_t', end_ea: 'ea_t'):
            """
            Constructs a basic block iterator for the specified function.

            Args:
                database: Reference to the active IDA database.
                start_ea: Start address of the function.
                end_ea: End address of the function.
            """
            self.m_database = database
            self.m_start_ea = start_ea
            self.m_end_ea = end_ea
            self.m_flowchart = None
            self.flowchart_created = False

        def create_flowchart(self) -> bool:
            """
            Helper function to create the flowchart.

            Returns:
                True if flowchart was created successfully, false otherwise.
            """
            if self.flowchart_created:
                return self.m_flowchart is not None

            try:
                # Create flowchart for the function
                self.m_flowchart = ida_gdl.qflow_chart_t()

                # Get function at start address
                import ida_funcs

                func = ida_funcs.get_func(self.m_start_ea)
                if func is None:
                    self.flowchart_created = True
                    return False

                # Generate flowchart
                self.m_flowchart.create('', func, func.start_ea, func.end_ea, 0)
                self.flowchart_created = True
                return True
            except Exception:
                self.m_flowchart = None
                self.flowchart_created = True
                return False

        def get_count(self) -> int:
            """
            Retrieves the number of basic blocks in the current range.

            Returns:
                The number of basic blocks.
            """
            if not self.m_database.is_open():
                ida_kernwin.warning(
                    f'{inspect.currentframe().f_code.co_name}: '
                    f'Database is not loaded. Please open a database first.'
                )
                return 0

            if not self.create_flowchart():
                ida_kernwin.warning(
                    f'{inspect.currentframe().f_code.co_name}: '
                    f'Failed to create flow chart for range start '
                    f'0x{self.m_start_ea:x}, end 0x{self.m_end_ea:x}.'
                )
                return 0

            if self.m_flowchart is None:
                return 0

            return self.m_flowchart.size()

        def get_at_index(self, index: int) -> 'qbasic_block_t':
            """
            Retrieves the basic block at the given index.

            Args:
                index: The index of the block.

            Returns:
                The qbasic_block_t at the specified index, or an empty block on error.
            """
            if not self.m_database.is_open():
                ida_kernwin.warning(
                    f'{inspect.currentframe().f_code.co_name}: '
                    f'Database is not loaded. Please open a database first.'
                )
                return ida_gdl.qbasic_block_t()

            if not self.create_flowchart():
                ida_kernwin.warning(
                    f'{inspect.currentframe().f_code.co_name}: '
                    f'Failed to create flow chart for range '
                    f'start 0x{self.m_start_ea:x}, end 0x{self.m_end_ea:x}.'
                )
                return ida_gdl.qbasic_block_t()

            if self.m_flowchart is None or index < 0 or index >= self.m_flowchart.size():
                ida_kernwin.warning(
                    f'{inspect.currentframe().f_code.co_name}: The index {index} is invalid.'
                )
                return ida_gdl.qbasic_block_t()

            return self.m_flowchart[index]

        def __iter__(self):
            """Python iterator protocol - matches SWIG extension."""
            count = self.get_count()
            for index in range(count):
                block = self.get_at_index(index)
                yield block

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
        if not self.m_database.is_open():
            ida_kernwin.warning(
                f'{inspect.currentframe().f_code.co_name}: '
                f'Database is not loaded. Please open a database first.'
            )
            return self.m_database.instructions.get_between(0, 0)

        if block is None or not hasattr(block, 'start_ea') or not hasattr(block, 'end_ea'):
            # Return empty iterator
            return self.m_database.instructions.get_between(0, 0)

        return self.m_database.instructions.get_between(block.start_ea, block.end_ea)

    def get_between(self, start_ea: 'ea_t', end_ea: 'ea_t') -> 'Iterator':
        """
        Retrieves all basic blocks between two addresses.

        Args:
            start_ea: Start address of the range.
            end_ea: End address of the range.

        Returns:
            A basic block iterator.
        """
        return self.Iterator(self.m_database, start_ea, end_ea)
