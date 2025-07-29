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

from os import path

from .winmem_decorators import *
from .winmem_types import *

ENABLE_LOGGING = False

# loading dll
_dll_name = path.dirname(path.abspath(__file__)) + \
            ("\\pywinmem64.dll" if not ENABLE_LOGGING else "\\pywinmem64_log.dll")
_dll = ctypes.CDLL(_dll_name)

# defining functions
def _validate_handle(handler: any, func_name: str | None) -> bool:
    if not handler:
        err_code = ctypes.get_last_error()
        if err_code != 0:
            f = func_name if func_name is not None or len(func_name) > 0 else "Function"
            raise RuntimeError(f"{f} failed with error code {err_code}")
        return False
    return True


def _validate_function_result(result, func_name: str | None) -> bool:
    if not result:
        err_code = ctypes.get_last_error()
        if err_code != 0:
            f = func_name if func_name is not None or len(func_name) > 0 else "Function"
            raise RuntimeError(f"{f} failed with WinAPI error: {err_code} ({err_code:X})")
        return False
    return True


_dll.GetWindowByName.argtypes = [LPCSTR]
_dll.GetWindowByName.restype = HWND
@winmem_args
def GetWindowByName(windowName: str) -> HWND:
    hwnd = _dll.GetWindowByName(windowName)

    if not _validate_handle(hwnd, "GetWindowByName"):
        raise RuntimeError("Unable to reach window handle")

    return hwnd


_dll.GetWindowByPID.argtypes = [DWORD]
_dll.GetWindowByPID.restype = HWND
def GetWindowByPID(processID: int) -> HWND:
    hwnd = _dll.GetWindowByPID(processID)

    if not _validate_handle(hwnd, "GetWindowByPID"):
        raise RuntimeError("Unable to reach window handle")

    return hwnd


_dll.GetPIDByName.argtypes = [LPCSTR]
_dll.GetPIDByName.restype = DWORD
@winmem_args
def GetPIDByName(processName: str) -> int:
    pid = _dll.GetPIDByName(processName)

    return pid


_dll.GetThreadInfo.argtypes = [DWORD, DWORD, pThreadInfo]
_dll.GetThreadInfo.restype = BOOL
def GetThreadInfo(threadID: int, processID: int) -> dict:
    if threadID < 0:
        raise WINMEM_ERROR_INVALID_TID
    if processID <= 0:
        raise WINMEM_ERROR_INVALID_PID

    info = ThreadInfo()
    result = _dll.GetThreadInfo(threadID, processID, REF(info))

    _validate_function_result(result, "GetThreadInfo")

    return {
        'thread_id': info.threadID,
        'owner_process_id': info.ownerProcessID,
        'base_priority': info.basePriority
    }


_dll.GetProcessInfo.argtypes = [LPCSTR, DWORD, pProcessInfo]
_dll.GetProcessInfo.restype = BOOL
@winmem_args
def GetProcessInfo(processName: str | None = None, processID: int = -1) -> dict:
    if processName is None and processID is None:
        raise ValueError("Please provide at least one correct argument")

    info = ProcessInfo()

    if processName is None:
        result = _dll.GetProcessInfo(b'0', processID, REF(info))
    else:
        result = _dll.GetProcessInfo(processName, processID, REF(info))

    _validate_function_result(result, "GetProcessInfo")

    return {
        'process_id': info.processID,
        'parent_process_id': info.parentProcessID,
        'thread_count': info.threadCount,
        'exe_path': bytes(info.exePath).decode()
    }


_dll.GetModuleInfo.argtypes = [LPCSTR, DWORD, pModuleInfo]
_dll.GetModuleInfo.restype = BOOL
@winmem_args
def GetModuleInfo(moduleName: str, processID: int) -> dict:
    if moduleName is None or len(moduleName) <= 0:
        raise ValueError("Module name is invalid")
    if processID is None or processID <= 0:
        raise WINMEM_ERROR_INVALID_PID

    info = ModuleInfo()
    result = _dll.GetModuleInfo(moduleName, processID, REF(info))

    _validate_function_result(result, "GetModuleInfo")

    return {
        'process_id': info.processID,
        'base_address': info.baseAddress,
        'base_size': info.baseSize,
        'module_handle': info.hModule,
        'name': bytes(info.name).decode()
    }


_dll.GetPIDByWindowName.argtypes = [LPCSTR]
_dll.GetPIDByWindowName.restype = DWORD
@winmem_args
def GetPIDByWindowName(windowName: str) -> int:
    if len(windowName) <= 0:
        raise ValueError("Window name is invalid")

    pid = _dll.GetPIDByWindowName(windowName)

    return pid


_dll.AttachByPID.argtypes = [DWORD, DWORD]
_dll.AttachByPID.restype = HANDLE
def AttachByPID(processId: int, access: int) -> HANDLE:
    if processId <= 0:
        raise WINMEM_ERROR_INVALID_PID
    if access <= 0:
        raise WINMEM_ERROR_PROCESSNOACCESS

    handle = _dll.AttachByPID(processId, access)

    if not _validate_handle(handle, "AttachByPID"):
        raise RuntimeError(f"Unable to attach to process {processId}")

    return handle


_dll.AttachByName.argtypes = [LPCSTR, DWORD]
_dll.AttachByName.restype = HANDLE
@winmem_args
def AttachByName(processName: str, access: int) -> HANDLE:
    if len(processName) <= 0:
        raise ValueError("Invalid process name")
    if access <= 0:
        raise WINMEM_ERROR_PROCESSNOACCESS

    handle = _dll.AttachByName(processName, access)

    if not _validate_handle(handle, "AttachByName"):
        raise RuntimeError(f"Unable to attach to process {processName}")

    return handle


_dll.AttachByWindowName.argtypes = [LPCSTR, DWORD]
_dll.AttachByWindowName.restype = HANDLE
@winmem_args
def AttachByWindowName(windowName: str, access: int) -> HANDLE:
    if len(windowName) <= 0:
        raise ValueError("Invalid window name")
    if access <= 0:
        raise WINMEM_ERROR_PROCESSNOACCESS

    handle = _dll.AttachByWindowName(windowName, access)

    if not _validate_handle(handle, "AttachByWindowName"):
        raise RuntimeError(f"Unable to attach to process of window {windowName}")

    return handle


_dll.AttachByWindow.argtypes = [HWND, DWORD]
_dll.AttachByWindow.restype = HANDLE
def AttachByWindow(hWindow: HWND, access: int) -> HANDLE:
    if not _validate_handle(hWindow, "AttachByWindow"):
        raise ValueError("Window handle is not accessible")
    if access <= 0:
        raise WINMEM_ERROR_PROCESSNOACCESS

    handle = _dll.AttachByWindow(hWindow, access)

    if not _validate_handle(handle, "AttachByWindow"):
        raise RuntimeError(f"Unable to attach to process")

    return handle


_dll.Detach.argtypes = [HANDLE]
_dll.Detach.restype = None
def Detach(hProcess: HANDLE):
    if not _validate_handle(hProcess, "Detach"):
        raise ValueError("Handle is not valid")

    _dll.Detach(hProcess)  # TODO change to Detach after lib update


_dll.EnumThreads.argtypes = [EnumThreadsCallback, void_p]
_dll.EnumThreads.restype = BOOL
def EnumThreads(callback, args: tuple = ()):
    if not callable(callback):
        raise WINMEM_ERROR_INVALID_CALLBACK

    def _callback(thread_info_p, _):
        result = callback(thread_info_p.contents, *args)
        return BOOL(True if result else False)

    _dll.EnumThreads(EnumThreadsCallback(_callback), None)


_dll.EnumProcesses.argtypes = [EnumProcessesCallback, void_p]
_dll.EnumProcesses.restype = BOOL
def EnumProcesses(callback, args: tuple = ()):
    if not callable(callback):
        raise WINMEM_ERROR_INVALID_CALLBACK

    def _callback(process_info_p, _):
        result = callback(process_info_p.contents, *args)
        return BOOL(True if result else False)

    _dll.EnumProcesses(EnumProcessesCallback(_callback), None)


_dll.EnumModules.argtypes = [DWORD, EnumModulesCallback, void_p]
_dll.EnumModules.restype = BOOL
def EnumModules(processID: int, callback, args: tuple = ()):
    if not callable(callback):
        raise WINMEM_ERROR_INVALID_CALLBACK
    if processID <= 0:
        raise WINMEM_ERROR_INVALID_PID

    def _callback(module_info_p, _):
        result = callback(module_info_p.contents, *args)
        return BOOL(True if result else False)

    _dll.EnumModules(processID, EnumModulesCallback(_callback), None)


_dll.GetMemoryInfo.argtypes = [HANDLE, LPCVOID, PMemoryBasicInfo]
_dll.GetMemoryInfo.restype = size_t
def GetMemoryInfo(hProcess: HANDLE, address: int) -> dict:
    if not _validate_handle(hProcess, "GetMemoryInfo"):
        raise RuntimeError("Handle to the process is not valid")

    mbi = MemoryBasicInfo()
    _dll.GetMemoryInfo(hProcess, LPCVOID(address), REF(mbi))

    return {
        'base_address': mbi.BaseAddress,
        'allocation_base': mbi.AllocationBase,
        'allocation_protect': mbi.AllocationProtect,
        'partition_id': mbi.PartitionId,
        'region_size': mbi.RegionSize,
        'state': mbi.State,
        'protect': mbi.Protect,
        'type': mbi.Type
    }


_dll.GetModuleBaseAddress.argtypes = [DWORD, LPCSTR]
_dll.GetModuleBaseAddress.restype = uint_ptr
@winmem_args
def GetModuleBaseAddress(processID: int, name: str) -> int:
    if processID <= 0:
        raise WINMEM_ERROR_INVALID_PID
    if name is None or len(name) <= 0:
        raise ValueError(f"Wrong module name: {name}")
    
    moduleBase = _dll.GetModuleBaseAddress(processID, name)

    return moduleBase


_dll.IsMemoryProtected.argtypes = [HANDLE, LPCVOID, DWORD]
_dll.IsMemoryProtected.restype = BOOL
def IsMemoryProtected(hProcess: HANDLE, address: int, protectionFlag: int) -> bool:
    if hProcess is None or not _validate_handle(hProcess, "_IsMemoryProtected"):
        raise WINMEM_ERROR_INVALID_HANDLE
    if address is None:
        raise ValueError("Invalid memory address")
    if protectionFlag is None or protectionFlag == 0:
        raise ValueError("Provided invalid protection flag")
    
    result = _dll.IsMemoryProtected(hProcess, LPCVOID(address), protectionFlag)

    return _validate_function_result(result, "IsMemoryProtected")


_dll.ProtectMemory.argtypes = [HANDLE, LPVOID, size_t, DWORD, PDWORD]
_dll.ProtectMemory.restype = BOOL
def ProtectMemory(hProcess: HANDLE, address: int, size: int, newProtect: int) -> int:
    if not _validate_handle(hProcess):
        raise WINMEM_ERROR_INVALID_HANDLE
    if address is None:
        raise ValueError("Invalid memory address")
    if size <= 0 or size is None:
        raise ValueError("Memory size cannot be negative or 0")
    if newProtect <= 0 or newProtect is None:
        raise ValueError("Please provide memory access flag")
    
    oldProtect = c_int(0)

    result = _dll.ProtectMemory(hProcess, LPVOID(address), size_t(size), newProtect, REF(oldProtect))

    if not _validate_function_result(result, "ProtectMemory"):
        return 0

    return oldProtect


_dll.ReadMemory.argtypes = [HANDLE, LPCVOID, LPVOID, size_t]
_dll.ReadMemory.restype = size_t
def ReadMemory(hProcess: HANDLE, address: int, size: int) -> tuple[bytes | None, int]:
    if not _validate_handle(hProcess, "ReadMemory"):
        raise WINMEM_ERROR_INVALID_HANDLE
    if address is None:
        raise ValueError("Invalid memory address")
    if size <= 0 or size is None:
        raise ValueError("Memory size cannot be negative or 0")
    
    buffer = (c_char * size)()
    
    n_bytes_read = _dll.ReadMemory(hProcess, LPCVOID(address), buffer, size_t(size))
    
    if not _validate_function_result(n_bytes_read, "ReadMemory"):
        return None, 0

    return bytes(buffer[:n_bytes_read]), n_bytes_read


_dll.WriteMemory.argtypes = [HANDLE, LPVOID, LPVOID, size_t]
_dll.WriteMemory.restype = size_t
def WriteMemory(hProcess: HANDLE, address: int, buffer: list | bytes, size: int) -> int:
    if not _validate_handle(hProcess, "WriteMemory"):
        raise WINMEM_ERROR_INVALID_HANDLE
    if address is None:
        raise ValueError("Invalid memory address")
    if buffer is None:
        raise ValueError("Invalid buffer")
    
    if isinstance(buffer, list):
        buffer = bytes(buffer)

    n_bytes_written = _dll.WriteMemory(hProcess, LPVOID(address), buffer, size_t(size))

    if not _validate_function_result(n_bytes_written, "WriteMemory"):
        return 0

    return n_bytes_written


_dll.PatternScan.argtypes = [HANDLE, PBYTE, size_t]
_dll.PatternScan.restype = uint_ptr
def PatternScan(hProcess: HANDLE, pattern: list | bytes) -> int:
    if not _validate_handle(hProcess, "PatternScan"):
        raise WINMEM_ERROR_INVALID_HANDLE
    if pattern is None or len(pattern) == 0:
        raise ValueError("Pattern should be at least 1 byte size")
    
    if isinstance(pattern, list):
        pattern = bytes(pattern)

    pattern_buffer = (c_ubyte * len(pattern))(*pattern)
    address = _dll.PatternScan(hProcess, PBYTE(pattern_buffer), size_t(len(pattern)))

    if not _validate_function_result(address, "PatternScan"):
        return 0

    return address


_dll.ApplyPatch.argtypes = [HANDLE, LPVOID, PBYTE, size_t, PBYTE]
_dll.ApplyPatch.restype = size_t
def ApplyPatch(hProcess: HANDLE, address: int, newBytes: bytes, size: int, oldBytes: bytearray) -> int:
    if not _validate_handle(hProcess, "ApplyPatch"):
        raise WINMEM_ERROR_INVALID_HANDLE
    if address is None or address == 0:
        raise WINMEM_ERROR_INVALID_ADDRESS
    if not isinstance(newBytes, bytes) and not isinstance(oldBytes, bytearray):
        raise ValueError(f"Wrong parameters type: newBytes, oldBytes (expected bytes)")
    if size is None or size <= 0:
        return 0
    
    new_bytes_buffer = (c_ubyte * len(newBytes)).from_buffer_copy(newBytes)
    old_bytes_buffer = (c_ubyte * len(oldBytes)).from_buffer(oldBytes)

    n_bytes_read = _dll.ReadMemory(hProcess, LPCVOID(address), old_bytes_buffer, size_t(size))
    if (not _validate_function_result(n_bytes_read, "ApplyPatch: ReadMemory")):
        raise WINMEM_ERROR_READMEM
    
    n_bytes_written = _dll.WriteMemory(hProcess, LPVOID(address), new_bytes_buffer, size_t(size))
    if (not _validate_function_result(n_bytes_written, "ApplyPatch: WriteMemory")):
        raise WINMEM_ERROR_WRITEMEM
    
    return n_bytes_written


_dll.RevertPatch.argtypes = [HANDLE, LPVOID, PBYTE, size_t]
_dll.RevertPatch.restype = size_t
def RevertPatch(hProcess: HANDLE, address: int, oldBytes: bytes, size: int) -> int:
    if not _validate_handle(hProcess, "ApplyPatch"):
        raise WINMEM_ERROR_INVALID_HANDLE
    if address is None or address == 0:
        raise WINMEM_ERROR_INVALID_ADDRESS
    if not isinstance(oldBytes, bytes):
        raise ValueError(f"Wrong parameter type: oldBytes (expected bytes)")
    if size is None or size <= 0:
        return 0
    
    restore_buffer = (c_ubyte * len(oldBytes)).from_buffer_copy(oldBytes)

    n_bytes_written = _dll.WriteMemory(hProcess, LPVOID(address), restore_buffer, size_t(size))
    if (not _validate_function_result(n_bytes_written, "ApplyPatch: WriteMemory")):
        raise WINMEM_ERROR_WRITEMEM
    
    return n_bytes_written

_dll.ExportMemory.argtypes = [HANDLE, LPCVOID, size_t]
_dll.ExportMemory.restype = size_t
def ExportMemory(hProcess: HANDLE, address: int, size: int) -> int:
    if not _validate_handle(hProcess, "ExportMemory"):
        raise WINMEM_ERROR_INVALID_HANDLE
    if address is None or address <= 0:
        raise ValueError("Invalid memory address")
    if size is None or size <= 0:
        return 0
    
    bytes_exported = _dll.ExportMemory(hProcess, LPCVOID(address), size_t(size))

    if not _validate_function_result(bytes_exported, "ExportMemory"):
        return 0
    
    return bytes_exported
