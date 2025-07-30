from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List

import ida_auto
import ida_diskio
import ida_funcs
import ida_idp
import ida_undo
import idapro

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from idadex import ea_t

    from .database import Database


logger = logging.getLogger(__name__)


class _FlirtHooks(ida_idp.IDB_Hooks):
    def __init__(self):
        ida_idp.IDB_Hooks.__init__(self)
        self.details = Details()

    def idasgn_matched_ea(self, ea, name, lib_name):
        self.details.matches += 1
        self.details.functions.append(DetailsEntry(addr=ea, name=name, lib=lib_name))


@dataclasses.dataclass
class DetailsEntry:
    addr: 'ea_t'
    name: str = ''
    lib: str = ''


@dataclasses.dataclass
class Details:
    path: str = ''
    matches: int = 0
    functions: List[DetailsEntry] = dataclasses.field(default_factory=list)


@decorate_all_methods(check_db_open)
class Flirt:
    """
    Provides access to FLIRT signature (.sig) files in the IDA database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a signature handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def apply(self, path: Path, probe_only: bool = False):
        """
        Applies signature files to current database.

        Args:
            path: Path to the signature file or directory with sig files.
            probe_only: If true, signature files are only probed (apply operation is undone).

        Returns:
            A list of signature details.
        """

        info = []
        if path.is_dir():
            for sig_path in path.rglob('*.sig'):
                info.append(self._apply(sig_path, probe_only))
        elif path.suffix == '.sig':
            info.append(self._apply(path, probe_only))

        return info

    def create(self, pat_only: bool = False) -> bool:
        """
        Create a signature file from current database.

        Args:
            pat_only: If true, generate only PAT file.

        Returns:
            True in case of successful creation.
        """
        return idapro.make_signatures(pat_only)

    def get_index(self, path: Path) -> int:
        """
        Get index of applied signature file.

        Args:
            path: Path to the signature file.

        Returns:
            Index of applied signature file, -1 if not found.
        """
        for index in range(0, ida_funcs.get_idasgn_qty()):
            name, _, _ = ida_funcs.get_idasgn_desc_with_matches(index)
            if name == str(path):
                return index
        return -1

    def get_files(self, directories: List[Path] = None) -> List[Path]:
        """
        Retrieves a list of available FLIRT signature (.sig) files.

        Args:
            directories: Optional list of paths to directories containing FLIRT signature files.

        Returns:
            A list of available signature file paths.
        """
        dir_list = [
            Path(ida_diskio.idadir(ida_diskio.SIG_SUBDIR)),
            Path(ida_diskio.idadir(ida_diskio.IDP_SUBDIR)),
        ]
        if directories:
            dir_list = dir_list + directories

        sig_files = []
        for directory in dir_list:
            if directory.is_dir():
                sig_files.extend(p.resolve() for p in directory.rglob('*.sig'))
        return sig_files

    def _apply(self, path: Path, probe_only: bool = False):
        hooks = _FlirtHooks()
        hooks.hook()
        if probe_only:
            ida_undo.create_undo_point('ida_domain_flirt', 'undo_point')
        ida_funcs.plan_to_apply_idasgn(str(path))
        ida_auto.auto_wait()
        hooks.unhook()
        entry = hooks.details
        entry.path = str(path)
        if probe_only:
            ida_undo.perform_undo()

        return entry
