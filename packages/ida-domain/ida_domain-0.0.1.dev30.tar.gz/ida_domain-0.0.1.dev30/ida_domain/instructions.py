from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Iterator, List, Optional

import ida_bytes
import ida_idp
import ida_kernwin
import ida_lines
import ida_ua

from .decorators import check_db_open, decorate_all_methods, check_insn_valid
from .operands import Operand, OperandFactory

if TYPE_CHECKING:
    from .database import Database


@decorate_all_methods(check_db_open)
class Instructions:
    """
    Provides access to instruction-related operations using structured operand hierarchy.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs an instructions handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def is_valid(self, insn: object) -> bool:
        """
        Checks if the given instruction is valid.

        Args:
            insn: The instruction to validate.

        Returns:
            `True` if the instruction is valid, `False` otherwise.
        """
        if insn is None:
            return False

        # Check if instruction has valid itype (instruction type)
        try:
            return hasattr(insn, 'itype') and insn.itype != 0
        except Exception:
            return False

    def decode(self, ea: int) -> ida_ua.insn_t | None:
        """
        Decodes the instruction at the specified address.

        Args:
            ea: The effective address of the instruction.

        Returns:
            An insn_t instance, if false returns None.
        """
        insn = ida_ua.insn_t()
        if ida_ua.decode_insn(insn, ea) > 0:
            return insn
        return None

    @check_insn_valid()
    def get_disassembly(self, insn: ida_ua.insn_t) -> str | None:
        """
        Retrieves the disassembled string representation of the given instruction.

        Args:
            insn: The instruction to disassemble.

        Returns:
            The disassembly as string, if fails, returns None.
        """
        try:
            # Generate disassembly line
            line = ida_lines.generate_disasm_line(
                insn.ea, ida_lines.GENDSM_MULTI_LINE | ida_lines.GENDSM_REMOVE_TAGS
            )
            if line:
                return line
            else:
                ida_kernwin.warning(
                    f'{inspect.currentframe().f_code.co_name}: '
                    f'Failed to generate disassembler line for address 0x{insn.ea:x}'
                )
                return None
        except Exception:
            ida_kernwin.warning(
                f'{inspect.currentframe().f_code.co_name}: '
                f'Failed to generate disasm line for address 0x{insn.ea:x}'
            )
            return None

    def get_between(self, start: int, end: int) -> Iterator[ida_ua.insn_t]:
        """
        Retrieves instructions between the specified addresses.

        Args:
            start: Start of the address range.
            end: End of the address range.

        Returns:
            An instruction iterator.
        """
        current = start
        while current < end:
            insn = ida_ua.insn_t()
            if ida_ua.decode_insn(insn, current) > 0:
                yield insn
            # Move to next instruction for next call
            current = ida_bytes.next_head(current, end)

    @check_insn_valid()
    def get_mnemonic(self, insn: ida_ua.insn_t) -> str | None:
        """
        Retrieves the mnemonic of the given instruction.

        Args:
            insn: The instruction to analyze.

        Returns:
            A string representing the mnemonic of the given instruction.
            If retrieving fails, returns None.
        """
        return ida_ua.print_insn_mnem(insn.ea)

    @check_insn_valid()
    def get_operands_count(self, insn: ida_ua.insn_t) -> int:
        """
        Retrieve the operands number of the given instruction.

        Args:
            insn: The instruction to analyze.

        Returns:
            An integer representing the number, if error, the number is negative.
        """
        count = 0
        for n in range(len(insn.ops)):
            if insn.ops[n].type == ida_ua.o_void:
                break
            count += 1
        return count

    @check_insn_valid()
    def get_operand(self, insn: ida_ua.insn_t, index: int) -> Optional[Operand] | None:
        """
        Get a specific operand from the instruction.

        Args:
            insn: The instruction to analyze.
            index: The operand index (0, 1, 2, etc.).

        Returns:
            An Operand instance of the appropriate type, or None
            if the index is invalid or operand is void.
        """
        if not (0 <= index < len(insn.ops)):
            return None

        op = insn.ops[index]
        if op.type == ida_ua.o_void:
            return None

        return OperandFactory.create(self.m_database, op, insn.ea)

    @check_insn_valid()
    def get_operands(self, insn: ida_ua.insn_t) -> List[Operand]:
        """
        Get all operands from the instruction.

        Args:
            insn: The instruction to analyze.

        Returns:
            A list of Operand instances of appropriate types (excludes void operands).
        """
        operands = []
        for i in range(len(insn.ops)):
            op = insn.ops[i]
            if op.type == ida_ua.o_void:
                break
            operand = OperandFactory.create(self.m_database, op, insn.ea)
            if operand:
                operands.append(operand)
        return operands

    @check_insn_valid()
    def is_call_instruction(self, insn: ida_ua.insn_t) -> bool:
        """
        Check if the instruction is a call instruction.

        Args:
            insn: The instruction to analyze.

        Returns:
            True if this is a call instruction.
        """
        try:
            # Get canonical feature flags for the instruction
            feature = insn.get_canon_feature()
            return bool(feature & ida_idp.CF_CALL)
        except Exception:
            return False

    @check_insn_valid()
    def is_jump_instruction(self, insn: ida_ua.insn_t) -> bool:
        """
        Check if the instruction is a jump instruction.

        Args:
            insn: The instruction to analyze.

        Returns:
            True if this is a jump instruction.
        """
        try:
            # Get canonical feature flags for the instruction
            feature = insn.get_canon_feature()
            return bool(feature & ida_idp.CF_JUMP)
        except Exception:
            return False

    @check_insn_valid()
    def is_return_instruction(self, insn: ida_ua.insn_t) -> bool:
        """
        Check if the instruction is a return instruction.

        Args:
            insn: The instruction to analyze.

        Returns:
            True if this is a return instruction.
        """
        try:
            # Get canonical feature flags for the instruction
            feature = insn.get_canon_feature()
            return bool(feature & ida_idp.CF_STOP)
        except Exception:
            return False
