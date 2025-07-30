from __future__ import annotations

import glob
import os
from typing import TYPE_CHECKING, List

import ida_diskio

if TYPE_CHECKING:
    from .database import Database


class SignatureFiles:
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

    def get_available_sig_files(self) -> List[str]:
        """
        Retrieves a list of available FLIRT signature (.sig) files.

        Returns:
            A list of available signature file paths.
        """
        sig_files = []
        dir_list = [
            ida_diskio.idadir(ida_diskio.SIG_SUBDIR),
            ida_diskio.idadir(ida_diskio.IDP_SUBDIR),
        ]

        for sig_dir in dir_list:
            try:
                search_pattern = os.path.join(sig_dir, '*/*.sig')
                found_files = glob.glob(search_pattern)

                for file_name in found_files:
                    file_path = os.path.abspath(file_name)
                    sig_files.append(file_path)

            except Exception:
                # Continue with next directory if this one fails
                continue

        return sig_files
