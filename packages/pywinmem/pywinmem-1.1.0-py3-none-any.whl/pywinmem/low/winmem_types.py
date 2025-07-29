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

import ctypes
import ctypes.wintypes as wintypes
from sys import maxsize as _SYSTEM_MAXSIZE
from platform import machine, system
from enum import IntFlag

# Win64 check
# dll files that this library use were built for win64 configurations
# check https://github.com/fuckinbusy/winmem for src code
is_windows_64: bool = (system() == "Windows" 
                       and machine().endswith('64') 
                       and _SYSTEM_MAXSIZE >= 2 ** 32)

if not is_windows_64:
    raise Exception("This library should only be used on Win64 machine.")


WINMEM_ERROR_INVALID_PID = ValueError("Process ID cannot be negative or 0")
WINMEM_ERROR_INVALID_TID = ValueError("Thread ID cannot be negative")
WINMEM_ERROR_NOCALLBACK = ValueError("Enum callback is not provided")
WINMEM_ERROR_INVALID_CALLBACK = ValueError("Callback must be a callable function")
WINMEM_ERROR_INVALID_ADDRESS = ValueError("Invalid memory address")
WINMEM_ERROR_PROCESSNOACCESS = ValueError("Don't have access to this process")
WINMEM_ERROR_INVALID_HANDLE = ValueError("Invalid handle")
WINMEM_ERROR_READMEM = RuntimeWarning("Something gone wrong while reading memory")
WINMEM_ERROR_WRITEMEM = RuntimeWarning("Something gone wrong while writing memory")

WINMEM_CALLBACK_STOP = False
WINMEM_CALLBACK_CONTINUE = True


class ProcessAccess(IntFlag):
    """Defines process access rights for memory operations.

    These flags specify the permissions required when attaching to a process.
    Used in `Process` class initialization and memory operations.

    Flags:
        VM_READ (0x0010):    Read access to the process's memory.
        VM_WRITE (0x0020):   Write access to the process's memory.
        VM_OPERATION (0x0008): Required for memory operations like allocating/freeing memory.

    Example:

        >>> access = ProcessAccess.VM_READ | ProcessAccess.VM_WRITE
        >>> proc = Process("target.exe", access)
    """
    VM_READ = 0x0010
    VM_WRITE = 0x0020
    VM_OPERATION = 0x0008


class MemoryAccess(IntFlag):
    """Defines memory protection flags for virtual memory regions.

    These flags are used to check or modify memory protection settings
    (e.g., in `protect_memory()` or `is_memory_protected()`).

    Flags:
        WINMEM_CANREAD (0x02 | 0x20):   Memory is readable.
        WINMEM_CANWRITE (0x04 | 0x40):  Memory is writable.
        WINMEM_CANCOPY (0x08 | 0x80):   Memory can be copied (e.g., for dumping).
        WINMEM_NOACCESS (0x01):          Memory is inaccessible (guard page).

    Note:
        Combined flags (e.g., `0x02 | 0x20`) represent platform-specific values
        for compatibility with Windows API constants (e.g., `PAGE_READONLY`).

    Example:
        
        >>> if proc.is_memory_protected(addr, MemoryAccess.WINMEM_CANWRITE):
        >>>     proc.write_memory(addr, data)
    """
    WINMEM_CANREAD = 0x02 | 0x20
    WINMEM_CANWRITE = 0x04 | 0x40
    WINMEM_CANCOPY = 0x08 | 0x80
    WINMEM_NOACCESS = 0x01

# ctypes
POINTER = ctypes.POINTER
REF = ctypes.byref
TYPEDEF_FUNC = ctypes.CFUNCTYPE
CHAR_ARRAY = ctypes.create_string_buffer

struct = ctypes.Structure
char = ctypes.c_char
void_p = ctypes.c_void_p
size_t = ctypes.c_size_t
c_int = ctypes.c_int
c_char = ctypes.c_char
c_ubyte = ctypes.c_ubyte
uint_ptr = ctypes.c_ulonglong if is_windows_64 else ctypes.c_uint

# wintypes
HANDLE = wintypes.HANDLE
HWND = wintypes.HWND
LPCSTR = wintypes.LPCSTR
# BOOL = wintypes.BOOL ## this one gives a lot of errors
BOOL = ctypes.c_bool
DWORD = wintypes.DWORD
WORD = wintypes.WORD
BYTE = wintypes.BYTE
PBYTE = wintypes.PBYTE
HMODULE = wintypes.HMODULE
LPCVOID = wintypes.LPCVOID
LPVOID = wintypes.LPVOID
PDWORD = wintypes.PDWORD

# win constants
MAX_PATH = wintypes.MAX_PATH
MAX_MODULE_NAME32 = 255


# structs
class ThreadInfo(struct):
    _fields_ = [
        ("threadID", DWORD),
        ("ownerProcessID", DWORD),
        ("basePriority", DWORD)
    ]


class ProcessInfo(struct):
    _fields_ = [
        ("processID", DWORD),
        ("parentProcessID", DWORD),
        ("threadCount", DWORD),
        ("exePath", char * MAX_PATH)
    ]


class ModuleInfo(struct):
    _fields_ = [
        ("processID", DWORD),
        ("baseAddress", uint_ptr),
        ("baseSize", DWORD),
        ("hModule", HMODULE),
        ("name", char * (MAX_MODULE_NAME32 + 1))
    ]


class MemoryBasicInfo(struct):
    _fields_ = [
        ("BaseAddress", void_p),
        ("AllocationBase", void_p),
        ("AllocationProtect", DWORD),
        ("PartitionId", WORD),
        ("RegionSize", size_t),
        ("State", DWORD),
        ("Protect", DWORD),
        ("Type", DWORD)
    ]


pThreadInfo = POINTER(ThreadInfo)
pProcessInfo = POINTER(ProcessInfo)
pModuleInfo = POINTER(ModuleInfo)
PMemoryBasicInfo = POINTER(MemoryBasicInfo)

# callbacks
EnumThreadsCallback = TYPEDEF_FUNC(BOOL, pThreadInfo, void_p)
EnumProcessesCallback = TYPEDEF_FUNC(BOOL, pProcessInfo, void_p)
EnumModulesCallback = TYPEDEF_FUNC(BOOL, pModuleInfo, void_p)
