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

import warnings

from .low import winmem_low as _wml
from .low.winmem_types import WINMEM_CALLBACK_STOP, WINMEM_CALLBACK_CONTINUE, ProcessAccess, MemoryAccess


class Enumerator:
    """Provides static methods for enumerating system processes, threads, and modules."""

    @staticmethod
    def enum_processes(callback, args: tuple = ()):
        """Enumerate all running processes in the system.

        Args:
            callback: A function that will be called for each process.
            args: Additional arguments to pass to the callback function.
        """
        _wml.EnumProcesses(callback, args)

    @staticmethod
    def enum_threads(callback, args: tuple = ()):
        """Enumerate all threads in the system.

        Args:
            callback: A function that will be called for each thread.
            args: Additional arguments to pass to the callback function.
        """
        _wml.EnumThreads(callback, args)

    @staticmethod
    def enum_modules(process_id: int, callback, args: tuple = ()):
        """Enumerate all modules loaded by a specific process.

        Args:
            process_id: The ID of the process whose modules will be enumerated.
            callback: A function that will be called for each module.
            args: Additional arguments to pass to the callback function.
        """
        _wml.EnumModules(process_id, callback, args)


class Thread:
    """Represents a thread in a process with its properties."""

    def __init__(self):
        """Initialize a Thread instance with default values."""
        self._MAX_PRIORITY = 31
        self._MIN_PRIORITY = 0

        self._thread_id: int | None = None
        self._owner_process_id: int | None = None
        self._base_priority: int | None = None

    @property
    def thread_id(self) -> int | None:
        """Get the thread ID."""
        return self._thread_id

    @property
    def owner_process_id(self) -> int | None:
        """Get the ID of the process that owns this thread."""
        return self._owner_process_id

    @property
    def base_priority(self) -> int | None:
        """Get the base priority of the thread."""
        return self._base_priority

    @thread_id.setter
    def thread_id(self, value: int):
        """Set the thread ID.

        Args:
            value: The thread ID to set.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._thread_id = value

    @owner_process_id.setter
    def owner_process_id(self, value: int):
        """Set the owner process ID.

        Args:
            value: The process ID to set.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._owner_process_id = value

    @base_priority.setter
    def base_priority(self, value: int):
        """Set the base priority of the thread.

        Args:
            value: The priority value to set.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._base_priority = value

    def __repr__(self) -> str:
        """Return a string representation of the Thread instance."""
        return \
            f"Thread(" \
            f"thread_id='{self._thread_id}', " \
            f"owner_process_id='{self._owner_process_id}', " \
            f"base_priority='{self._base_priority} | {self._MAX_PRIORITY}')"


class Module:
    """Represents a module loaded by a process with its properties."""

    def __init__(self):
        """Initialize a Module instance with default values."""
        self._process_id: int | None = None
        self._base_address: int | None = None
        self._base_size: int | None = None
        self._handle: int | None = None
        self._name: str | None = None

    @property
    def process_id(self) -> int | None:
        """Get the ID of the process that loaded this module."""
        return self._process_id

    @property
    def base_address(self) -> int | None:
        """Get the base address of the module in memory."""
        return self._base_address

    @property
    def base_size(self) -> int | None:
        """Get the size of the module in memory."""
        return self._base_size

    @property
    def handle(self) -> int | None:
        """Get the handle of the module."""
        return self._handle

    @property
    def name(self) -> str | None:
        """Get the name of the module."""
        return self._name

    @process_id.setter
    def process_id(self, value: int):
        """Set the process ID.

        Args:
            value: The process ID to set.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._process_id = value

    @base_address.setter
    def base_address(self, value: int):
        """Set the base address of the module.

        Args:
            value: The base address to set.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._base_address = value

    @base_size.setter
    def base_size(self, value: int):
        """Set the size of the module.

        Args:
            value: The size to set.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._base_size = value

    @handle.setter
    def handle(self, value: int):
        """Set the handle of the module.

        Args:
            value: The handle to set.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(value, int):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._handle = value

    @name.setter
    def name(self, value: str):
        """Set the name of the module.

        Args:
            value: The name to set.

        Raises:
            ValueError: If the value is not a string.
        """
        if not isinstance(value, str):
            raise ValueError(f"Wrong type of value: {type(value)}")
        self._name = value

    def __repr__(self) -> str:
        """Return a string representation of the Module instance."""
        return \
            f"Module(" \
            f"process_id='{self._process_id}', " \
            f"base_address='{hex(self._base_address) if self._base_address is not None else self._base_address}', " \
            f"base_size='{self._base_size}', " \
            f"name='{self._name}')"


class Process:
    """Represents a process with methods to interact with its memory and modules."""

    def __init__(self, process_name: str, process_access: int):
        """Initialize a Process instance.

        Args:
            process_name: The name of the process to attach to.
            process_access: The access rights required for the process.
        """
        self._process_id: int = 0
        self._parent_process_id: int = 0
        self._threads_count: int = 0
        self._name: str = process_name
        self._base_module: Module | None = None
        self._modules: list[Module] = []
        self._threads: list[Thread] = []
        self._access: int = process_access
        self._handle = None
        self._is_managed: bool = False

    def _get_all_threads(self):
        def callback(thread_info, threads: list[Thread]):
            if thread_info.ownerProcessID == self._process_id:
                thread = Thread()
                thread.thread_id = thread_info.threadID
                thread.owner_process_id = thread_info.ownerProcessID
                thread.base_priority = thread_info.basePriority
                threads.append(thread)
            return WINMEM_CALLBACK_CONTINUE

        Enumerator.enum_threads(callback, tuple([self._threads]))

    def _get_all_modules(self):
        def callback(module_info, modules: list[Module]) -> bool:
            module = Module()
            module.process_id = module_info.processID
            module.base_address = module_info.baseAddress
            module.base_size = module_info.baseSize
            module.handle = module_info.hModule
            module.name = module_info.name.decode()
            modules.append(module)
            return WINMEM_CALLBACK_CONTINUE

        Enumerator.enum_modules(self._process_id, callback, tuple([self._modules]))

    def _find_process(self) -> bool:
        data = [self._name, False]

        def callback(process_info, find_data: list):
            process_name = find_data[0]
            if process_info.exePath.decode() == process_name:
                find_data[1] = True
                return WINMEM_CALLBACK_STOP
            return WINMEM_CALLBACK_CONTINUE

        Enumerator.enum_processes(callback, tuple([data]))
        return data[1]

    def attach(self):
        """Attach to the process.

        Raises:
            RuntimeError: If the process is not found or already attached.
        """
        if not self._find_process():
            raise RuntimeError("Process not found")
        if self._handle is not None:
            raise RuntimeError("Process is already attached")

        process_info: dict = _wml.GetProcessInfo(self._name)

        self._process_id: int = process_info.get('process_id')
        self._parent_process_id: int = process_info.get('parent_process_id')
        self._threads_count: int = process_info.get('thread_count')
        self._handle = _wml.AttachByPID(self._process_id, self._access)

        if not self._handle:
            raise RuntimeError("Cannot attach to this process")

        self._get_all_modules()
        self._get_all_threads()

        self._base_module: Module = self._modules[0]

        return self

    def __enter__(self) -> "Process":
        """Enter the context manager for the process.

        Returns:
            Process: The attached process instance.

        Raises:
            RuntimeError: If the process is already attached.
        """
        if self._handle is not None or self._is_managed:
            raise RuntimeError("Process is already attached")
        self._is_managed = True
        return self.attach()

    def get_memory_info(self, address: int) -> dict:
        """Get memory protection information for a specific address.

        Args:
            address: The memory address to query.

        Returns:
            dict: A dictionary containing memory protection information.
        """
        return _wml.GetMemoryInfo(self._handle, address)

    def is_memory_protected(self, address: int, protect_flag: MemoryAccess | int) -> bool:
        """Checks if a memory region is protected with the specified protection flag.

        Args:
            address: The memory address to check.
            protect_flag: The protection flag to verify.

        Returns:
            bool: True if the memory is protected, False otherwise.
        """
        return _wml.IsMemoryProtected(self._handle, address, protect_flag)

    def protect_memory(self, address: int, size: int, new_protect_flag: MemoryAccess | int) -> int:
        """Change the protection of a memory region.

        Args:
            address: The starting address of the memory region.
            size: The size of the memory region.
            new_protect_flag: The new protection flag to apply.

        Returns:
            int: The old protection flag.
        """
        return _wml.ProtectMemory(self._handle, address, size, new_protect_flag)

    def read_memory(self, address: int, size: int) -> tuple[bytes | None, int]:
        """Read memory from the process.

        Args:
            address: The starting address to read from.
            size: The number of bytes to read.

        Returns:
            tuple: A tuple containing the read bytes (or None) and the number of bytes read.
        """
        return _wml.ReadMemory(self._handle, address, size)

    def write_memory(self, address: int, buffer: list | bytes, size: int) -> int:
        """Write memory to the process.

        Args:
            address: The starting address to write to.
            buffer: The data to write.
            size: The number of bytes to write.

        Returns:
            int: The number of bytes written.
        """
        return _wml.WriteMemory(self._handle, address, buffer, size)

    def pattern_scan(self, pattern: list | bytes) -> int:
        """Scan the process memory for a specific pattern.

        Args:
            pattern: The byte pattern to search for.

        Returns:
            int: The address where the pattern was found, or 0 if not found.
        """
        return _wml.PatternScan(self._handle, pattern)

    def apply_patch(self, address:int, new_bytes: bytes, old_bytes: bytearray, size: int) -> int:
        """Applies memory patch.

        Args:
            address: The starting address to write to.
            new_bytes: The data to write.
            old_bytes: The bytes array for old data to be stored in.
            size: The number of bytes to write.

        Returns:
            int: The number of bytes patched.
        """
        return _wml.ApplyPatch(self._handle, address, new_bytes, size, old_bytes)

    def revert_patch(self, address: int, old_bytes: bytes, size: int) -> int:
        """Reverts memory patch (restores memory).

        Args:
            address: The starting address to write to.
            old_bytes: Old data to be restored.
            size: The number of bytes to write.

        Returns:
            int: The number of bytes restored.
        """
        return _wml.RevertPatch(self._handle, address, old_bytes, size)

    def export_memory(self, address: int, size: int) -> int:
        """Export a memory region to a file.

        Args:
            address: The starting address of the memory region.
            size: The size of the memory region.

        Returns:
            int: The status code of the operation.
        """
        return _wml.ExportMemory(self._handle, address, size)

    @property
    def process_id(self) -> int:
        """Get the process ID."""
        return self._process_id

    @property
    def parent_process_id(self) -> int:
        """Get the parent process ID."""
        return self._parent_process_id

    @property
    def threads_count(self) -> int:
        """Get the number of threads in the process."""
        return self._threads_count

    @property
    def name(self) -> str:
        """Get the name of the process."""
        return self._name

    @property
    def base_module(self) -> Module:
        """Get the base module of the process."""
        return self._base_module

    @property
    def handle(self) -> int:
        """Get the handle of the process."""
        return self._handle

    @property
    def modules(self) -> list[Module]:
        """Get a list of all modules loaded by the process."""
        return self._modules

    @property
    def threads(self) -> list[Thread]:
        """Get a list of all threads in the process."""
        return self._threads

    def detach(self):
        """Detach from the process."""
        if self._handle is not None:
            _wml.Detach(self._handle)
            self._handle = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and detach from the process."""
        if self._is_managed:
            self.detach()

    def __del__(self):
        """Destructor to ensure the process is detached."""
        if hasattr(self, "_handle") and self._handle is not None:
            warnings.warn(f"Process {self._name} has not been detached! Use 'with' or 'detach()'.", ResourceWarning)
            self.detach()
