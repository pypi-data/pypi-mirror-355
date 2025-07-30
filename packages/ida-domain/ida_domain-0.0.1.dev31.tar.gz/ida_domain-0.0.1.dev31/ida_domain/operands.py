from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Any
from enum import IntEnum
import re
import ida_ua
import ida_name
import ida_idp
import ida_lines

# Import IDA operand type constants for easier access
O_VOID = ida_ua.o_void
O_REG = ida_ua.o_reg
O_MEM = ida_ua.o_mem
O_PHRASE = ida_ua.o_phrase
O_DISPL = ida_ua.o_displ
O_IMM = ida_ua.o_imm
O_FAR = ida_ua.o_far
O_NEAR = ida_ua.o_near
O_IDPSPEC0 = ida_ua.o_idpspec0
O_IDPSPEC5 = ida_ua.o_idpspec5
OF_OUTER_DISP = ida_ua.OF_OUTER_DISP

if TYPE_CHECKING:
    from .database import Database


class OperandType(IntEnum):
    """Enumeration of operand types for easier identification."""

    VOID = O_VOID
    REGISTER = O_REG
    MEMORY = O_MEM
    PHRASE = O_PHRASE
    DISPLACEMENT = O_DISPL
    IMMEDIATE = O_IMM
    FAR_ADDRESS = O_FAR
    NEAR_ADDRESS = O_NEAR
    PROCESSOR_SPECIFIC_0 = O_IDPSPEC0
    PROCESSOR_SPECIFIC_1 = ida_ua.o_idpspec1
    PROCESSOR_SPECIFIC_2 = ida_ua.o_idpspec2
    PROCESSOR_SPECIFIC_3 = ida_ua.o_idpspec3
    PROCESSOR_SPECIFIC_4 = ida_ua.o_idpspec4
    PROCESSOR_SPECIFIC_5 = O_IDPSPEC5


class OperandDataType(IntEnum):
    """Enumeration of operand data types."""

    BYTE = ida_ua.dt_byte
    WORD = ida_ua.dt_word
    DWORD = ida_ua.dt_dword
    QWORD = ida_ua.dt_qword
    FLOAT = ida_ua.dt_float
    DOUBLE = ida_ua.dt_double
    TBYTE = ida_ua.dt_tbyte
    PACKREAL = ida_ua.dt_packreal
    BYTE16 = ida_ua.dt_byte16
    BYTE32 = ida_ua.dt_byte32
    BYTE64 = ida_ua.dt_byte64
    HALF = ida_ua.dt_half
    FWORD = ida_ua.dt_fword
    BITFIELD = ida_ua.dt_bitfild
    STRING = ida_ua.dt_string
    UNICODE = ida_ua.dt_unicode
    LDBL = ida_ua.dt_ldbl
    CODE = ida_ua.dt_code
    VOID = ida_ua.dt_void


@dataclass(frozen=True)
class OperandInfo:
    """Basic information about an operand."""

    number: int
    type_name: str
    data_type_name: str
    size_bytes: int
    size_bits: Optional[int] = None
    flags: Optional[str] = None
    is_hidden: bool = False
    special_value: Optional[str] = None
    is_floating_point: bool = False
    is_read: bool = False
    is_write: bool = False
    access_type: Optional[str] = None

    def __post_init__(self):
        if self.size_bits is None:
            object.__setattr__(self, 'size_bits', self.size_bytes * 8)


@dataclass(frozen=True)
class RegisterInfo:
    """Information about a register operand."""

    register_number: int
    register_name: str

    def __post_init__(self):
        if self.register_number < 0:
            raise ValueError(f'Invalid register number: {self.register_number}')


@dataclass(frozen=True)
class ImmediateInfo:
    """Information about an immediate operand."""

    value: int
    hex_value: str
    is_address: bool
    symbol_name: Optional[str] = None
    signed_32bit: Optional[int] = None

    def __post_init__(self):
        # Auto-generate hex representation if not provided
        if not self.hex_value:
            object.__setattr__(self, 'hex_value', f'0x{self.value:x}')

        # Auto-generate signed interpretation for large values
        if self.signed_32bit is None and self.value > 0x80000000:
            object.__setattr__(self, 'signed_32bit', self.value - 0x100000000)


@dataclass(frozen=True)
class AddressingInfo:
    """Information about memory operand addressing."""

    addressing_type: str
    formatted_string: Optional[str] = None
    # Direct memory fields
    address: Optional[int] = None
    symbol_name: Optional[str] = None
    # Register-based fields
    phrase_number: Optional[int] = None
    displacement: Optional[int] = None
    outer_displacement: Optional[int] = None
    has_outer_displacement: bool = False

    def is_direct_memory(self) -> bool:
        """Check if this is direct memory addressing."""
        return self.addressing_type == 'direct_memory'

    def is_register_based(self) -> bool:
        """Check if this uses register-based addressing."""
        return self.addressing_type in ('register_indirect', 'register_displacement')

    def has_displacement(self) -> bool:
        """Check if this addressing mode has any displacement."""
        return self.displacement is not None or self.outer_displacement is not None


@dataclass(frozen=True)
class ProcessorSpecificInfo:
    """Information about processor-specific operands."""

    spec_type: int
    value: int
    addr: int
    reg: int
    phrase: int
    specval: int
    flags: int


class Operand(ABC):
    """Abstract base class for all operand types."""

    def __init__(self, database: 'Database', operand: ida_ua.op_t, instruction_ea: int):
        self.m_database = database
        self._op = operand
        self._instruction_ea = instruction_ea

    @property
    def raw_operand(self) -> ida_ua.op_t:
        """Get the underlying op_t object."""
        return self._op

    @property
    def number(self) -> int:
        """Get the operand number (0, 1, 2, etc.)."""
        return self._op.n

    @property
    def type(self) -> OperandType:
        """Get the operand type as an enum."""
        return OperandType(self._op.type)

    @property
    def data_type(self) -> OperandDataType:
        """Get the operand data type as an enum."""
        return OperandDataType(self._op.dtype)

    @property
    def flags(self) -> int:
        """Get the operand flags."""
        return self._op.flags

    @property
    def is_shown(self) -> bool:
        """Check if the operand should be displayed."""
        return self._op.shown()

    @property
    def size_bytes(self) -> int:
        """Get the size of the operand in bytes."""
        return ida_ua.get_dtype_size(self._op.dtype)

    @property
    def size_bits(self) -> int:
        """Get the size of the operand in bits."""
        return self.size_bytes * 8

    @property
    def specval(self) -> int:
        """Get the special value field."""
        return self._op.specval

    def is_floating_point(self) -> bool:
        """Check if this is a floating point operand."""
        return ida_ua.is_floating_dtype(self._op.dtype)

    def get_data_type_name(self) -> str:
        """Get a human-readable name for the operand data type."""
        data_type_names = {
            OperandDataType.BYTE: 'byte',
            OperandDataType.WORD: 'word',
            OperandDataType.DWORD: 'dword',
            OperandDataType.QWORD: 'qword',
            OperandDataType.FLOAT: 'float',
            OperandDataType.DOUBLE: 'double',
            OperandDataType.TBYTE: 'tbyte',
            OperandDataType.PACKREAL: 'packreal',
            OperandDataType.BYTE16: 'byte16',
            OperandDataType.BYTE32: 'byte32',
            OperandDataType.BYTE64: 'byte64',
            OperandDataType.HALF: 'half',
            OperandDataType.FWORD: 'fword',
            OperandDataType.BITFIELD: 'bitfield',
            OperandDataType.STRING: 'string',
            OperandDataType.UNICODE: 'unicode',
            OperandDataType.LDBL: 'ldbl',
            OperandDataType.CODE: 'code',
            OperandDataType.VOID: 'void',
        }
        return data_type_names.get(self.data_type, f'unknown_{self.data_type}')

    def is_read(self) -> bool:
        """Check if this operand is read (used) by the instruction."""
        try:
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, self._instruction_ea):
                return False
            ph = ida_idp.get_ph()
            feature = ph.get_canon_feature(insn.itype)
            return ida_idp.has_cf_use(feature, self.number)
        except Exception:
            return False

    def is_write(self) -> bool:
        """Check if this operand is written (modified) by the instruction."""
        try:
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, self._instruction_ea):
                return False
            ph = ida_idp.get_ph()
            feature = ph.get_canon_feature(insn.itype)
            return ida_idp.has_cf_chg(feature, self.number)
        except Exception:
            return False

    def get_access_type(self) -> str:
        """Get a string description of how this operand is accessed."""
        is_read = self.is_read()
        is_write = self.is_write()

        if is_read and is_write:
            return 'read_write'
        elif is_read:
            return 'read'
        elif is_write:
            return 'write'
        else:
            return 'none'

    def _get_base_info(self) -> OperandInfo:
        """Get base operand information common to all operands."""
        return OperandInfo(
            number=self.number,
            type_name=self.get_type_name(),
            data_type_name=self.get_data_type_name(),
            size_bytes=self.size_bytes,
            size_bits=self.size_bits if self.size_bits != self.size_bytes * 8 else None,
            flags=f'0x{self.flags:x}' if self.flags != 0 else None,
            is_hidden=not self.is_shown,
            special_value=f'0x{self.specval:x}' if self.specval != 0 else None,
            is_floating_point=self.is_floating_point(),
            is_write=self.is_write(),
            is_read=self.is_read(),
            access_type=self.get_access_type(),
        )

    @abstractmethod
    def get_type_name(self) -> str:
        """Get a human-readable name for the operand type."""
        pass

    @abstractmethod
    def get_value(self) -> Any:
        """Get the primary value of the operand."""
        pass

    def get_register_info(self) -> RegisterInfo:
        """Get detailed register information."""
        return RegisterInfo(
            register_number=self.register_number, register_name=self.get_register_name()
        )

    def get_info(self) -> OperandInfo:
        """Get structured information about the operand."""
        return self._get_base_info()

    def __repr__(self) -> str:
        return self.__str__()


class RegisterOperand(Operand):
    """Operand representing a processor register (o_reg)."""

    @property
    def register_number(self) -> int:
        """Get the register number."""
        return self._op.reg

    def get_type_name(self) -> str:
        return 'register'

    def get_value(self) -> int:
        return self.register_number

    def get_register_name(self) -> str:
        """Get the name of this register using the operand's size."""
        try:
            return ida_idp.get_reg_name(self.register_number, self.size_bytes)
        except Exception:
            reg_names = ida_idp.ph_get_regnames()
            if self.register_number < len(reg_names):
                return reg_names[self.register_number]
            return f'reg{self.register_number}'

    def get_info(self) -> OperandInfo:
        return self._get_base_info()

    def __str__(self) -> str:
        reg_name = self.get_register_name()
        access_type = self.get_access_type()
        return f'RegisterOperand(Op{self.number}, {reg_name}, {access_type})'


class ImmediateOperand(Operand):
    """Operand representing immediate values (o_imm, o_far, o_near)."""

    def get_type_name(self) -> str:
        if self.type == OperandType.IMMEDIATE:
            return 'immediate'
        elif self.type == OperandType.FAR_ADDRESS:
            return 'far_address'
        elif self.type == OperandType.NEAR_ADDRESS:
            return 'near_address'
        else:
            return 'immediate'

    def get_value(self) -> int:
        """Get the immediate value or address."""
        if self.type in (OperandType.FAR_ADDRESS, OperandType.NEAR_ADDRESS):
            return self._op.addr
        else:
            return self._op.value

    def is_address(self) -> bool:
        """Check if this is an address operand (far/near)."""
        return self.type in (OperandType.FAR_ADDRESS, OperandType.NEAR_ADDRESS)

    def has_outer_displacement(self) -> bool:
        """Check if this operand has an outer displacement.

        Returns True if the OF_OUTER_DISP flag is set.
        """
        return bool(self._op.flags & OF_OUTER_DISP)

    def get_name(self) -> Optional[str]:
        """Get the symbolic name for address operands."""
        if self.is_address():
            name = ida_name.get_name(self.get_value())
            return name if name else None
        return None

    def get_hex_value(self) -> str:
        """Get hex representation of the value."""
        value = self.get_value()
        return f'0x{value:x}'

    def get_signed_32bit(self) -> Optional[int]:
        """Get signed 32-bit interpretation for large values."""
        value = self.get_value()
        if value > 0x80000000:
            return value - 0x100000000
        return None

    def get_immediate_info(self) -> ImmediateInfo:
        """Get detailed immediate information."""
        value = self.get_value()
        return ImmediateInfo(
            value=value,
            hex_value=self.get_hex_value(),
            is_address=self.is_address(),
            symbol_name=self.get_name(),
            signed_32bit=self.get_signed_32bit(),
        )

    def get_info(self) -> OperandInfo:
        return self._get_base_info()

    def __str__(self) -> str:
        value = self.get_value()
        if self.is_address():
            name = self.get_name()
            addr_str = name if name else f'0x{value:x}'
            return f'ImmediateOperand(Op{self.number}, {self.get_type_name()}, {addr_str})'
        else:
            return f'ImmediateOperand(Op{self.number}, 0x{value:x})'


class MemoryOperand(Operand):
    """Operand representing memory access (o_mem, o_phrase, o_displ)."""

    def get_type_name(self) -> str:
        if self.type == OperandType.MEMORY:
            return 'direct_memory'
        elif self.type == OperandType.PHRASE:
            return 'register_indirect'
        elif self.type == OperandType.DISPLACEMENT:
            return 'register_displacement'
        else:
            return 'memory'

    def get_value(self) -> Any:
        """Get the primary value based on memory type."""
        if self.type == OperandType.MEMORY:
            return self._op.addr
        elif self.type == OperandType.PHRASE:
            return self._op.phrase
        elif self.type == OperandType.DISPLACEMENT:
            return {'phrase': self._op.phrase, 'displacement': self._op.addr}
        else:
            return self._op.addr

    def is_direct_memory(self) -> bool:
        """Check if this is direct memory access."""
        return self.type == OperandType.MEMORY

    def is_register_based(self) -> bool:
        """Check if this uses register-based addressing."""
        return self.type in (OperandType.PHRASE, OperandType.DISPLACEMENT)

    def get_address(self) -> Optional[int]:
        """Get the address for direct memory operands."""
        if self.type == OperandType.MEMORY:
            return self._op.addr
        elif self.type == OperandType.DISPLACEMENT:
            return self._op.addr  # displacement value
        return None

    def get_phrase_number(self) -> Optional[int]:
        """Get the phrase number for register-based operands."""
        if self.is_register_based():
            return self._op.phrase
        return None

    def get_displacement(self) -> Optional[int]:
        """Get the base displacement value.

        This is the primary displacement used in addressing modes like [reg + disp].
        Stored in op_t.addr field.
        """
        if self.type == OperandType.DISPLACEMENT:
            return self._op.addr
        return None

    def get_outer_displacement(self) -> Optional[int]:
        """Get the outer displacement value for complex addressing modes.

        Used in processors like 68k for nested addressing: ([reg + disp1], disp2)
        where disp1 is base displacement and disp2 is outer displacement.
        Only present when OF_OUTER_DISP flag is set. Stored in op_t.value field.
        """
        if (
            self.type == OperandType.DISPLACEMENT
            and self._op.value
            and self.has_outer_displacement()
        ):
            return self._op.value
        return None

    def has_outer_displacement(self) -> bool:
        """Check if this operand has an outer displacement.

        Returns True if the OF_OUTER_DISP flag is set.
        """
        return bool(self._op.flags & ida_ua.OF_OUTER_DISP)

    def get_name(self) -> Optional[str]:
        """Get the symbolic name for direct memory operands."""
        if self.type == OperandType.MEMORY:
            name = ida_name.get_name(self._op.addr)
            return name if name else None
        return None

    def get_formatted_string(self) -> Optional[str]:
        """Get the formatted operand string from IDA."""
        try:
            ret = ida_ua.print_operand(self._instruction_ea, self.number)
            return ida_lines.tag_remove(ret)
        except Exception:
            return None

    def get_addressing_info(self) -> AddressingInfo:
        """Get detailed addressing information."""
        if self.is_direct_memory():
            return AddressingInfo(
                addressing_type=self.get_type_name(),
                formatted_string=self.get_formatted_string(),
                address=self.get_address(),
                symbol_name=self.get_name(),
            )
        elif self.is_register_based():
            return AddressingInfo(
                addressing_type=self.get_type_name(),
                formatted_string=self.get_formatted_string(),
                phrase_number=self.get_phrase_number(),
                displacement=self.get_displacement()
                if self.type == OperandType.DISPLACEMENT
                else None,
                outer_displacement=self.get_outer_displacement()
                if self.type == OperandType.DISPLACEMENT
                else None,
                has_outer_displacement=self.has_outer_displacement()
                if self.type == OperandType.DISPLACEMENT
                else False,
            )
        else:
            return AddressingInfo(
                addressing_type=self.get_type_name(), formatted_string=self.get_formatted_string()
            )

    def get_sib_components(
        self,
    ) -> tuple[Optional[str], Optional[str], Optional[int], Optional[int]]:
        """Get SIB components: (base_register, index_register, scale, displacement).

        Returns:
            tuple: (base_reg, index_reg, scale, displacement) or (None, None, None, None) if fails
        """
        formatted = self.get_formatted_string()
        if not formatted:
            return (None, None, None, None)

        # Simple regex patterns
        bracket_match = re.search(r'\[([^\]]+)\]', formatted)
        if not bracket_match:
            return (None, None, None, None)

        content = bracket_match.group(1)

        # Parse components
        base_reg = None
        index_reg = None
        scale = None
        displacement = None

        # Look for register*scale pattern (e.g., rdi*2)
        scale_match = re.search(r'(\w+)\*([1248])', content)
        if scale_match:
            index_reg = scale_match.group(1)
            scale = int(scale_match.group(2))

        # Look for displacement (numbers with + or -)
        disp_match = re.search(r'([+-]\d+|[+-]0x[0-9a-fA-F]+)', content)
        if disp_match:
            disp_str = disp_match.group(1)
            if disp_str.startswith(('+', '-')):
                displacement = int(disp_str, 0)  # handles both decimal and hex

        # Find base register (first register that's not the index)
        reg_matches = re.findall(r'\b([a-z]{2,3}\d?)\b', content)
        for reg in reg_matches:
            if reg != index_reg:
                base_reg = reg
                break

        return (base_reg, index_reg, scale, displacement)

    def get_base_register(self) -> Optional[str]:
        """Get the base register name (e.g., 'rsi', 'rbp')."""
        base, _, _, _ = self.get_sib_components()
        return base

    def get_index_register(self) -> Optional[str]:
        """Get the index register name (e.g., 'rdi', 'rcx')."""
        _, index, _, _ = self.get_sib_components()
        return index

    def get_scale(self) -> Optional[int]:
        """Get the scale factor (1, 2, 4, or 8)."""
        _, _, scale, _ = self.get_sib_components()
        return scale

    def get_sib_displacement(self) -> Optional[int]:
        """Get the displacement value from SIB addressing."""
        _, _, _, displacement = self.get_sib_components()
        return displacement or self.get_displacement()  # fallback to existing method

    def get_info(self) -> OperandInfo:
        return self._get_base_info()

    def __str__(self) -> str:
        if self.type == OperandType.MEMORY:
            addr = self.get_address()
            name = self.get_name()
            addr_str = f'[{name}]' if name else f'[0x{addr:x}]'
            return f'MemoryOperand(Op{self.number}, direct, {addr_str})'
        else:
            addressing_str = self.get_formatted_string()
            if addressing_str:
                return f'MemoryOperand(Op{self.number}, {self.get_type_name()}, {addressing_str})'
            else:
                return f'MemoryOperand(Op{self.number}, {self.get_type_name()})'


class ProcessorSpecificOperand(Operand):
    """Operand representing processor-specific types (o_idpspec0-5)."""

    def __init__(self, database: 'Database', operand: ida_ua.op_t, instruction_ea: int):
        super().__init__(database, operand, instruction_ea)
        self._spec_type = operand.type - O_IDPSPEC0

    def get_type_name(self) -> str:
        return f'processor_specific_{self._spec_type}'

    def get_value(self) -> Any:
        """Return raw value for processor-specific operands."""
        return self._op.value

    def get_spec_type(self) -> int:
        """Get the processor-specific type number (0-5)."""
        return self._spec_type

    def get_processor_info(self) -> ProcessorSpecificInfo:
        """Get all potentially relevant fields for processor-specific operands."""
        return ProcessorSpecificInfo(
            spec_type=self._spec_type,
            value=self._op.value,
            addr=self._op.addr,
            reg=self._op.reg,
            phrase=self._op.phrase,
            specval=self._op.specval,
            flags=self._op.flags,
        )

    def get_info(self) -> OperandInfo:
        return self._get_base_info()

    def __str__(self) -> str:
        return (
            f'ProcessorSpecificOperand(Op{self.number}, type={self._spec_type}, '
            f'value=0x{self._op.value:x})'
        )


class OperandFactory:
    """Factory for creating appropriate operand instances."""

    @staticmethod
    def create(
        database: 'Database', operand: ida_ua.op_t, instruction_ea: int
    ) -> Optional[Operand]:
        """Create an operand instance based on the operand type."""
        if not operand:
            return None

        op_type = operand.type

        if op_type == O_VOID:
            return None
        elif op_type == O_REG:
            return RegisterOperand(database, operand, instruction_ea)
        elif op_type in (O_IMM, O_FAR, O_NEAR):
            return ImmediateOperand(database, operand, instruction_ea)
        elif op_type in (O_MEM, O_PHRASE, O_DISPL):
            return MemoryOperand(database, operand, instruction_ea)
        elif op_type >= O_IDPSPEC0 and op_type <= O_IDPSPEC5:
            return ProcessorSpecificOperand(database, operand, instruction_ea)
        else:
            # Unknown operand type, treat as processor-specific
            return ProcessorSpecificOperand(database, operand, instruction_ea)
