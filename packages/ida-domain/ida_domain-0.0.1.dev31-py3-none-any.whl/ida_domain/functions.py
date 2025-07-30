from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, List, Optional

import ida_bytes
import ida_funcs
import ida_hexrays
import ida_kernwin
import ida_lines
import ida_name
import ida_typeinf

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from ida_funcs import func_t
    from idadex import ea_t

    from .basic_blocks import BasicBlocks
    from .database import Database
    from .instructions import Instructions


@decorate_all_methods(check_db_open)
class Functions:
    """
    Provides access to function-related operations within the database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a functions handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_between(self, start: 'ea_t', end: 'ea_t'):
        """
        Retrieves functions between specified addresses.

        Args:
            start: Start address of the range.
            end: End address of the range.

        Returns:
            A functions iterator.
        """
        for i in range(ida_funcs.get_func_qty()):
            func = ida_funcs.getn_func(i)
            if func and start <= func.start_ea < end:
                yield func
            if func.start_ea > end:
                return

    def get_all(self):
        """
        Retrieves all functions in the database.

        Returns:
            A functions iterator covering the entire database range.
        """
        from ida_ida import inf_get_max_ea, inf_get_min_ea

        return self.get_between(inf_get_min_ea(), inf_get_max_ea())

    def get_at(self, ea: 'ea_t') -> Optional['func_t']:
        """
        Retrieves the function associated with the given address.

        Args:
            ea: An effective address within the function body.

        Returns:
            A pointer to the corresponding function (`func_t*`), or `nullptr` on failure.
        """
        return ida_funcs.get_func(ea)

    def get_name(self, func: 'func_t') -> str:
        """
        Retrieves the name of the given function.

        Args:
            func: The function instance.

        Returns:
            The function's name as a string, or an empty string on failure.
        """
        if func is None:
            ida_kernwin.warning(f'{inspect.currentframe().f_code.co_name}: Invalid parameters')
            return ''

        return ida_name.get_name(func.start_ea)

    def set_name(self, func: 'func_t', name: str) -> bool:
        """
        Renames the given function.

        Args:
            func: The function instance.
            name: The new name to assign to the function.

        Returns:
            True on success, false otherwise.
        """
        if func is None:
            ida_kernwin.warning(f'{inspect.currentframe().f_code.co_name}: Invalid parameters')
            return False

        # Pass SN_NOCHECK, let IDA sanitize the name for us
        # Doing it for consistency, this is the only behaviour for renaming a segment
        # Trying to adopt a common behaviour for renaming entities
        return ida_name.set_name(func.start_ea, name, ida_name.SN_NOCHECK)

    def get_basic_blocks(self, func: 'func_t') -> 'BasicBlocks.Iterator':
        """
        Retrieves the basic blocks that compose the given function.

        Args:
            func: The function instance.

        Returns:
            An iterator for the function's basic blocks.
        """
        if func is None:
            # Return empty iterator
            return self.m_database.basic_blocks.get_between(0, 0)
        return self.m_database.basic_blocks.get_between(func.start_ea, func.end_ea)

    def get_instructions(self, func: 'func_t') -> 'Instructions.Iterator':
        """
        Retrieves all instructions within the given function.

        Args:
            func: The function instance.

        Returns:
            An instruction iterator for the function.
        """
        if func is None:
            ida_kernwin.warning(f'{inspect.currentframe().f_code.co_name}: Invalid parameters')
            return self.m_database.instructions.get_between(0, 0)

        return self.m_database.instructions.get_between(func.start_ea, func.end_ea)

    def get_disassembly(self, func: 'func_t') -> List[str]:
        """
        Retrieves the disassembly lines for the given function.

        Args:
            func: The function instance.

        Returns:
            A vector of strings, each representing a line of disassembly.
        """
        if func is None:
            ida_kernwin.warning(f'{inspect.currentframe().f_code.co_name}: Invalid parameters')
            return []

        lines = []
        ea = func.start_ea
        while ea < func.end_ea:
            line = ida_lines.generate_disasm_line(
                ea, ida_lines.GENDSM_MULTI_LINE | ida_lines.GENDSM_REMOVE_TAGS
            )
            if line:
                lines.append(line)
            ea = ida_bytes.next_head(ea, func.end_ea)
        return lines

    def get_pseudocode(self, func: 'func_t', remove_tags: bool = True) -> List[str]:
        """
        Retrieves the decompiled pseudocode of the given function.

        Args:
            func: The function instance.
            remove_tags: Remove the tags, return a cleaned line.

        Returns:
            A vector of strings, each representing a line of pseudocode.
        """
        if func is None:
            ida_kernwin.warning(f'{inspect.currentframe().f_code.co_name}: Invalid parameters')
            return []

        try:
            # Try to decompile the function
            cfunc = ida_hexrays.decompile(func.start_ea)
            if cfunc is None:
                return []

            # Get the pseudocode
            pseudocode = []
            sv = cfunc.get_pseudocode()
            for i in range(len(sv)):
                line = sv[i].line
                if remove_tags:
                    line = ida_lines.tag_remove(line)
                pseudocode.append(line)
            return pseudocode
        except Exception:
            return []

    def get_signature(self, func: 'func_t') -> str:
        """
        Retrieves the function's type signature.

        Args:
            func: The function instance.

        Returns:
            The signature as a string, or an empty string if unavailable.
        """
        if func is None:
            ida_kernwin.warning(f'{inspect.currentframe().f_code.co_name}: Invalid parameters')
            return ''

        return ida_typeinf.idc_get_type(func.start_ea) or ''

    def matches_signature(self, func: 'func_t', signature: str) -> bool:
        """
        Checks if a function matches the given signature.

        Args:
            func: The function instance.
            signature: The signature string to compare.

        Returns:
            True if the function matches, false otherwise.
        """
        if func is None:
            ida_kernwin.warning(f'{inspect.currentframe().f_code.co_name}: Invalid parameters')
            return False

        return self.get_signature(func) == signature

    def create(self, ea: 'ea_t') -> bool:
        """
        Creates a new function at the specified address.

        Args:
            ea: The effective address to start the function.

        Returns:
            True if the function was successfully created, false otherwise.
        """
        return ida_funcs.add_func(ea)

    def remove(self, ea: 'ea_t') -> bool:
        """
        Deletes the function at the specified address.

        Args:
            ea: The effective address of the function to remove.

        Returns:
            True if the function was successfully removed, false otherwise.
        """
        return ida_funcs.del_func(ea)
