# pywinmem - Windows memory manipulation toolkit
# Copyright (C) 2025 fuckin_busy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""Low-level Windows memory operations."""
from .winmem_low import *
from .winmem_types import *

__all__ = [
    # Functions
    'GetWindowByName',
    'GetWindowByPID',
    'GetPIDByName',
    'GetThreadInfo',
    'GetProcessInfo',
    'GetModuleInfo',
    'GetPIDByWindowName',
    'AttachByPID',
    'AttachByName',
    'AttachByWindowName',
    'AttachByWindow',
    'Detach',
    'EnumThreads',
    'EnumProcesses',
    'EnumModules',
    'GetMemoryInfo',
    'GetModuleBaseAddress',
    'IsMemoryProtected',
    'ProtectMemory',
    'ReadMemory',
    'WriteMemory',
    'PatternScan',
    'ExportMemory',

    # Types and constants
    'ProcessAccess',
    'MemoryAccess',
    'WINMEM_ERROR_INVALID_PID',
    'WINMEM_ERROR_INVALID_TID',
    'WINMEM_ERROR_NOCALLBACK',
    'WINMEM_ERROR_INVALID_CALLBACK',
    'WINMEM_ERROR_PROCESSNOACCESS',
    'WINMEM_ERROR_INVALID_HANDLE',
    'WINMEM_CALLBACK_STOP',
    'WINMEM_CALLBACK_CONTINUE'
]
