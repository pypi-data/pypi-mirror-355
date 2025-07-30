from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, List

import ida_kernwin

if TYPE_CHECKING:
    pass


class IdaCommandBuilder:
    def __init__(self):
        self._auto_analysis = True
        self._autonomous = False
        self._has_loading_address = False
        self._loading_address = 0
        self._new_database = False
        self._has_compiler = False
        self._compiler = ''
        self._first_pass_directives = []
        self._second_pass_directives = []
        self._disable_fpp = False
        self._has_entry_point = False
        self._entry_point = 0
        self._jit_debugger = None
        self._log_file = None
        self._disable_mouse = False
        self._plugin_options = None
        self._output_database = None
        self._processor = None
        self._db_compression = None  # 'compress', 'pack', 'no_pack'
        self._run_debugger = None
        self._load_resources = False
        self._script_file = None
        self._script_args = []
        self._file_type = None
        self._file_member = None
        self._empty_database = False
        self._windows_dir = None
        self._no_segmentation = False
        self._debug_flags = 0
        self._use_text_mode = False

    def use_text_mode(self):
        self._use_text_mode = True
        return self

    def auto_analysis(self, enabled=True):
        self._auto_analysis = enabled
        return self

    def autonomous(self, enabled=True):
        self._autonomous = enabled
        return self

    def set_loading_address(self, address: int):
        self._has_loading_address = True
        self._loading_address = address
        return self

    def new_database(self, enabled=True):
        self._new_database = enabled
        return self

    def set_compiler(self, name: str, abi: str = ''):
        self._has_compiler = True
        self._compiler = f'{name}:{abi}' if abi else name
        return self

    def add_first_pass_directive(self, directive: str):
        self._first_pass_directives.append(directive)
        return self

    def add_second_pass_directive(self, directive: str):
        self._second_pass_directives.append(directive)
        return self

    def disable_fpp_instructions(self, disabled=True):
        self._disable_fpp = disabled
        return self

    def set_entry_point(self, address: int):
        self._has_entry_point = True
        self._entry_point = address
        return self

    def set_jit_debugger(self, enabled=True):
        self._jit_debugger = int(enabled)
        return self

    def set_log_file(self, filename: str):
        self._log_file = filename
        return self

    def disable_mouse(self, disabled=True):
        self._disable_mouse = disabled
        return self

    def set_plugin_options(self, options: str):
        self._plugin_options = options
        return self

    def set_output_database(self, path: str):
        self._output_database = path
        self._new_database = True
        return self

    def set_processor(self, processor_type: str):
        self._processor = processor_type
        return self

    def compress_database(self):
        self._db_compression = 'compress'
        return self

    def pack_database(self):
        self._db_compression = 'pack'
        return self

    def no_pack_database(self):
        self._db_compression = 'no_pack'
        return self

    def run_debugger(self, options: str = ''):
        self._run_debugger = options
        return self

    def load_resources(self, enabled=True):
        self._load_resources = enabled
        return self

    def run_script(self, script_file: str, args: List[str] = []):
        self._script_file = script_file
        self._script_args = args
        return self

    def set_file_type(self, file_type: str, member: str = ''):
        self._file_type = file_type
        self._file_member = member
        return self

    def empty_database(self, enabled=True):
        self._empty_database = enabled
        return self

    def set_windows_directory(self, directory: str):
        self._windows_dir = directory
        return self

    def no_segmentation(self, enabled=True):
        self._no_segmentation = enabled
        return self

    def set_debug_flags(self, flags):
        if isinstance(flags, int):
            self._debug_flags = flags
        elif isinstance(flags, list):
            self._debug_flags = self._parse_debug_flag_names(flags)
        return self

    def build_args(self):
        args = []

        if not self._auto_analysis:
            args.append('-a')
        if self._autonomous:
            args.append('-A')
        if self._has_loading_address:
            args.append(f'-b{self._loading_address:X}')
        if self._new_database:
            args.append('-c')
        if self._has_compiler:
            args.append(f'-C{self._compiler}')
        args += [f'-d{d}' for d in self._first_pass_directives]
        args += [f'-D{d}' for d in self._second_pass_directives]
        if self._disable_fpp:
            args.append('-f')
        if self._has_entry_point:
            args.append(f'-i{self._entry_point:X}')
        if self._jit_debugger is not None:
            args.append(f'-I{self._jit_debugger}')
        if self._log_file:
            args.append(f'-L{self._log_file}')
        if self._disable_mouse:
            args.append('-M')
        if self._output_database:
            args.append(f'-o{self._output_database}')
        if self._plugin_options:
            args.append(f'-O{self._plugin_options}')
        if self._processor:
            args.append(f'-p{self._processor}')
        if self._db_compression:
            comp_map = {'compress': '-P+', 'pack': '-P', 'no_pack': '-P-'}
            args.append(comp_map[self._db_compression])
        if self._run_debugger is not None:
            args.append(f'-r{self._run_debugger}')
        if self._load_resources:
            args.append('-R')
        if self._script_file:
            full = self._script_file + ''.join(
                f' {self._quote_if_needed(arg)}' for arg in self._script_args
            )
            args.append(f'-S"{full}"' if self._script_args else f'-S{self._script_file}')
        if self._empty_database:
            args.append('-t')
        if self._file_type:
            type_spec = f'-T{self._file_type}'
            if self._file_member:
                type_spec += f':{self._file_member}'
            args.append(type_spec)
        if self._windows_dir:
            args.append(f'-W{self._windows_dir}')
        if self._no_segmentation:
            args.append('-x')
        if self._debug_flags != 0:
            args.append(f'-z{self._debug_flags:X}')

        return ' '.join(args)

    def _quote_if_needed(self, s: str) -> str:
        return f'"{s}"' if ' ' in s else s

    def _parse_debug_flag_names(self, flag_names: List[str]) -> int:
        flag_map = {
            'drefs': 0x00000001,
            'offsets': 0x00000002,
            'flirt': 0x00000004,
            'idp': 0x00000008,
            'ldr': 0x00000010,
            'plugin': 0x00000020,
            'ids': 0x00000040,
            'config': 0x00000080,
            'heap': 0x00000100,
            'licensing': 0x00000200,
            'demangler': 0x00000400,
            'queue': 0x00000800,
            'rollback': 0x00001000,
            'already_data_or_code': 0x00002000,
            'type_system': 0x00004000,
            'notifications': 0x00008000,
            'debugger': 0x00010000,
            'debugger_appcall': 0x00020000,
            'source_debugger': 0x00040000,
            'accessibility': 0x00080000,
            'network': 0x00100000,
            'stack_analysis': 0x00200000,
            'debug_info': 0x00400000,
            'lumina': 0x00800000,
        }

        value = 0
        for name in flag_names:
            if name in flag_map:
                value |= flag_map[name]
            else:
                ida_kernwin.warning(
                    f"{inspect.currentframe().f_code.co_name}: Unknown debug flag '{name}'"
                )
        return value

    @property
    def auto_analysis_enabled(self) -> bool:
        return self._auto_analysis
