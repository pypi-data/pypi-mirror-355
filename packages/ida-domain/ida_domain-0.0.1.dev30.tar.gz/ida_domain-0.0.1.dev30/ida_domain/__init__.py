from __future__ import annotations

import logging
from logging import NullHandler
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version('ida-domain')
except PackageNotFoundError:
    # package is not installed
    pass

import builtins

# Check if IDA Python is already loaded
try:
    import ida_kernwin

    need_idapro = ida_kernwin.is_ida_library(None, 0, None)
except ImportError:
    need_idapro = True

if need_idapro:
    import idapro

    builtins.idapro = idapro  # Make idapro available inside other module files

# If we reach this point kernel libraries were successfully loaded
__all__ = ['Database', 'IdaCommandBuilder']

from .database import Database
from .ida_command_builder import IdaCommandBuilder

logging.getLogger(__name__).addHandler(NullHandler())
