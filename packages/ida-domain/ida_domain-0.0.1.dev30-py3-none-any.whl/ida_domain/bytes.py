from __future__ import annotations

import inspect
import struct
from typing import TYPE_CHECKING

import ida_bytes
import ida_ida
import ida_kernwin
import ida_lines

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from .database import Database


@decorate_all_methods(check_db_open)
class Bytes:
    """
    Handles operations related to raw data access from the IDA database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a bytes handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_byte(self, ea: int) -> int | None:
        """
        Retrieves a byte at the specified address.

        Args:
            ea: The effective address.

        Returns:
            The byte value, if error returns None.
        """
        try:
            value = ida_bytes.get_byte(ea)
            return value
        except Exception:
            return None

    def get_word(self, ea: int) -> int | None:
        """
        Retrieves a word (2 bytes) at the specified address.

        Args:
            ea: The effective address.

        Returns:
            The word value, if error returns None.
        """
        try:
            value = ida_bytes.get_word(ea)
            return value
        except Exception:
            return None

    def get_dword(self, ea: int) -> int | None:
        """
        Retrieves a double word (4 bytes) at the specified address.

        Args:
            ea: The effective address.

        Returns:
            The dword value, if error returns None.
        """
        try:
            value = ida_bytes.get_dword(ea)
            return value
        except Exception:
            return None

    def get_qword(self, ea: int) -> int | None:
        """
        Retrieves a quad word (8 bytes) at the specified address.

        Args:
            ea: The effective address.

        Returns:
            The qword value, if error returns None.
        """
        try:
            return ida_bytes.get_qword(ea)
        except Exception:
            return None

    def get_float(self, ea: int) -> float | None:
        """
        Retrieves a float value at the specified address.

        Args:
            ea: The effective address.

        Returns:
            The float value, if error returns None.
        """
        # Get data element size for float
        try:
            size = ida_bytes.get_data_elsize(ea, ida_bytes.float_flag())
        except Exception:
            return None

        if size <= 0 or size > 16:
            return None

        # Read bytes from address
        data = ida_bytes.get_bytes(ea, size)
        if data is None or len(data) != size:
            func_name = inspect.currentframe().f_code.co_name
            ida_kernwin.warning(f'{func_name}: Failed to read float from address 0x{ea:x}\n')
            return None

        # Convert bytes to float
        try:
            # Get processor endianness
            is_little_endian = not ida_ida.inf_is_be()
            endian = '<' if is_little_endian else '>'

            if size == 4:
                # IEEE 754 single precision
                value = struct.unpack(f'{endian}f', data)[0]
            elif size == 8:
                # IEEE 754 double precision (treat as float)
                double_value = struct.unpack(f'{endian}d', data)[0]
                value = float(double_value)
            else:
                # Handle other float sizes
                func_name = inspect.currentframe().f_code.co_name
                ida_kernwin.warning(
                    f'{func_name}: Failed to interpret float from address 0x{ea:x}\n'
                )
                return None

        except (struct.error, ValueError, OverflowError):
            func_name = inspect.currentframe().f_code.co_name
            ida_kernwin.warning(
                f'{func_name}: Failed to convert to float value from address 0x{ea:x}\n'
            )
            return None

        return value

    def get_double(self, ea: int) -> float | None:
        """
        Retrieves a double (floating-point) value at the specified address.

        Args:
            ea: The effective address.

        Returns:
            The double value, if error returns None.
        """
        # Get data element size for double
        try:
            size = ida_bytes.get_data_elsize(ea, ida_bytes.double_flag())
        except Exception:
            return None

        if size <= 0 or size > 16:
            return None

        # Read bytes from address
        data = ida_bytes.get_bytes(ea, size)
        if data is None or len(data) != size:
            func_name = inspect.currentframe().f_code.co_name
            ida_kernwin.warning(f'{func_name}: Failed to read double from address 0x{ea:x}\n')
            return None

        # Convert bytes to double
        try:
            # Get processor endianness
            is_little_endian = not ida_ida.inf_is_be()
            endian = '<' if is_little_endian else '>'

            if size == 8:
                # IEEE 754 double precision
                value = struct.unpack(f'{endian}d', data)[0]
            elif size == 4:
                # Single precision treated as double
                float_value = struct.unpack(f'{endian}f', data)[0]
                value = float(float_value)
            else:
                # Handle other double sizes
                func_name = inspect.currentframe().f_code.co_name
                ida_kernwin.warning(
                    f'{func_name}: Failed to interpret double from address 0x{ea:x}\n'
                )
                return None

        except (struct.error, ValueError, OverflowError):
            func_name = inspect.currentframe().f_code.co_name
            ida_kernwin.warning(
                f'{func_name}: Failed to convert to double value from address 0x{ea:x}\n'
            )
            return None

        return value

    def get_disassembly(self, ea: int) -> str | None:
        """
        Retrieves the disassembly text at a specified address.

        Args:
            ea: The effective address.

        Returns:
            A the disassembly string, if error returns None
        """
        try:
            # Generate disassembly line with multi-line and remove tags flags
            line = ida_lines.generate_disasm_line(
                ea, ida_lines.GENDSM_MULTI_LINE | ida_lines.GENDSM_REMOVE_TAGS
            )
            if line:
                return line
            else:
                func_name = inspect.currentframe().f_code.co_name
                ida_kernwin.warning(
                    f'{func_name}: Failed to generate disasm line for address 0x{ea:x}.\n'
                )
                return None
        except Exception:
            func_name = inspect.currentframe().f_code.co_name
            ida_kernwin.warning(
                f'{func_name}: Failed to generate disasm line for address 0x{ea:x}.\n'
            )
            return None
