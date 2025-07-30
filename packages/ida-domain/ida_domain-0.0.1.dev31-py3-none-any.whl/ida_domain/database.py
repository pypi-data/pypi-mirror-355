from __future__ import annotations

import inspect
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional

import ida_entry
import ida_ida
import ida_idaapi
import ida_kernwin
import ida_loader
import ida_nalt

from .basic_blocks import BasicBlocks
from .bytes import Bytes
from .comments import Comments
from .decorators import check_db_open
from .functions import Functions
from .ida_command_builder import IdaCommandBuilder
from .instructions import Instructions
from .names import Names
from .segments import Segments
from .signature_files import SignatureFiles
from .strings import Strings
from .types import Types
from .xrefs import Xrefs

if TYPE_CHECKING:
    from idadex import ea_t

    from .basic_blocks import BasicBlocks
    from .instructions import Instructions


class Database:
    """
    Provides access and control over the loaded IDA database.
    """

    def __init__(self):
        """
        Constructs a new interface to the IDA database.

        Note:
            When running inside IDA, this refers to the currently open database.
            Use open() to load a new database when using IDA as a library.
        """

    def open(self, db_path: str, db_args: Optional[IdaCommandBuilder] = None) -> bool:
        """
        Opens a database from the specified file path.

        Args:
            db_path: Path to the input file.
            db_args: Command builder responsible for passing arguments to IDA kernel.

        Returns:
            True if the database was successfully opened, false otherwise.

        Note:
            This function is available only when running IDA as a library.
            When running inside the IDA GUI, simply construct a Database() instance
            to refer to the currently open database. Use is_open() to check if a
            database is loaded.
        """
        if ida_kernwin.is_ida_library(None, 0, None):
            run_auto_analysis = True if db_args is None else db_args.auto_analysis_enabled
            # We can open a new database only in the context of idalib
            import idapro

            res = idapro.open_database(
                db_path, run_auto_analysis, '' if db_args is None else db_args.build_args()
            )
            if res != 0:
                ida_kernwin.warning(
                    f'{inspect.currentframe().f_code.co_name}: Failed to open database {db_path}'
                )
                return False
            return True
        else:
            # No database available
            ida_kernwin.warning(
                f'{inspect.currentframe().f_code.co_name}: '
                f'Open is available only when running as a library.'
            )
            return False

    def is_open(self) -> bool:
        # import traceback
        """
        Checks if the database is loaded.

        Returns:
            True if a database is open, false otherwise.
        """
        idb_path = ida_loader.get_path(ida_loader.PATH_TYPE_IDB)
        # if idb_path is None or idb_path == "":
        #     traceback.print_stack()
        #     print(f"----------------- {idb_path}    --")
        return idb_path is not None and len(idb_path) > 0

    @check_db_open
    def close(self, save: bool) -> None:
        """
        Closes the currently open database.

        Args:
            save: If true, saves changes before closing; otherwise, discards them.

        Note:
            This function is available only when running IDA as a library.
            When running inside the IDA GUI, we have no control on the database lifecycle.
        """
        if ida_kernwin.is_ida_library(None, 0, None):
            import idapro

            idapro.close_database(save)
        else:
            ida_kernwin.warning(
                f'{inspect.currentframe().f_code.co_name}: '
                f'Close is available only when running as a library.'
            )

    # Properties for Python-friendly access
    @property
    @check_db_open
    def entry_point(self) -> 'ea_t':
        """
        The entry point address of the binary.
        """
        return ida_entry.get_entry(ida_entry.get_entry_ordinal(0))

    @property
    @check_db_open
    def current_ea(self) -> 'ea_t':
        """
        The current effective address (equivalent to the "screen EA" in IDA GUI).
        """
        return ida_kernwin.get_screen_ea()

    @current_ea.setter
    @check_db_open
    def current_ea(self, ea: int) -> None:
        """
        Sets the current effective address (equivalent to the "screen EA" in IDA GUI).
        """
        if ida_kernwin.is_ida_library(None, 0, None):
            import idapro

            idapro.set_screen_ea(ea)
        else:
            ida_kernwin.jumpto(ea)

    @property
    @check_db_open
    def minimum_ea(self) -> 'ea_t':
        """
        The minimum effective address from this database.
        """
        return ida_ida.inf_get_min_ea()

    @property
    @check_db_open
    def maximum_ea(self) -> 'ea_t':
        """
        The maximum effective address from this database.
        """
        return ida_ida.inf_get_max_ea()

    @property
    @check_db_open
    def metadata(self) -> Dict[str, str]:
        """
        Map of key-value metadata about the current database.
        """
        metadata = {}

        # Get input file path
        input_path = ida_nalt.get_input_file_path()
        if input_path:
            metadata['path'] = input_path

        # Get module name
        module_name = ida_nalt.get_root_filename()
        if module_name:
            metadata['module'] = module_name

        # Get image base
        base_addr = ida_nalt.get_imagebase()
        if base_addr != ida_idaapi.BADADDR:
            metadata['base'] = ida_kernwin.ea2str(base_addr)

        # Get file size
        file_size = ida_nalt.retrieve_input_file_size()
        if file_size > 0:
            metadata['filesize'] = str(file_size)

        # Get MD5 hash
        md5_hash = ida_nalt.retrieve_input_file_md5()
        if md5_hash:
            metadata['md5'] = md5_hash.hex()

        # Get SHA256 hash
        sha256_hash = ida_nalt.retrieve_input_file_sha256()
        if sha256_hash:
            metadata['sha256'] = sha256_hash.hex()

        # Get CRC32
        crc32 = ida_nalt.retrieve_input_file_crc32()
        if crc32 != 0:
            metadata['crc32'] = str(crc32)

        # Get architecture
        arch = ida_ida.inf_get_procname()
        if arch:
            metadata['architecture'] = arch

        # Get bitness
        bitness = ida_ida.inf_get_app_bitness()
        if bitness > 0:
            metadata['bitness'] = str(bitness)

        # Get file format
        file_format = ida_loader.get_file_type_name()
        if file_format:
            metadata['format'] = file_format

        # Get load time
        ctime = ida_nalt.get_idb_ctime()
        if ctime:
            metadata['load_time'] = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')

        return metadata

    @property
    def segments(self) -> Segments:
        """Handler that provides access to memory segment-related operations."""
        return Segments(self)

    @property
    def functions(self) -> Functions:
        """Handler that provides access to function-related operations."""
        return Functions(self)

    @property
    def basic_blocks(self) -> BasicBlocks:
        """Handler that provides access to basic block-related operations."""
        return BasicBlocks(self)

    @property
    def instructions(self) -> Instructions:
        """Handler that provides access to instruction-related operations."""
        return Instructions(self)

    @property
    def comments(self) -> Comments:
        """Handler that provides access to user comment-related operations."""
        return Comments(self)

    @property
    def strings(self) -> Strings:
        """Handler that provides access to string-related operations."""
        return Strings(self)

    @property
    def names(self) -> Names:
        """Handler that provides access to name-related operations."""
        return Names(self)

    @property
    def types(self) -> Types:
        """Handler that provides access to type-related operations."""
        return Types(self)

    @property
    def bytes(self) -> Bytes:
        """Handler that provides access to byte-level memory operations."""
        return Bytes(self)

    @property
    def signature_files(self) -> SignatureFiles:
        """Handler that provides access to signature file operations."""
        return SignatureFiles(self)

    @property
    def xrefs(self) -> Xrefs:
        """Handler that provides access to cross-reference (xref) operations."""
        return Xrefs(self)
