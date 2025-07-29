# PyWinMem

Windows memory manipulation toolkit for Python.

## Features
- Enumerate processes/threads/modules
- Read/write process memory
- Pattern scanning
- Memory protection management

## Installation
```bash
pip install pywinmem
```

## Basic usage
```python
# Sample usage of pywinmem library

from pywinmem import Process, ProcessAccess, MemoryAccess

# Example process name and access rights
process_name = "example_process.exe"  # Replace with the actual process name
access_rights = ProcessAccess.ALL_ACCESS

# Using context manager to attach to the process
with Process(process_name, access_rights) as process:
    print(f"Attached to process: {process_name} with PID: {process.process_id}")

    # Read memory from the process
    address = 0x1000  # Replace with the actual memory address to read from
    size = 4  # Number of bytes to read
    value, bytes_read = process.read_memory(address, size)
    print(f"Read {bytes_read} bytes from address {hex(address)}: {value}")

    # Write memory to the process
    new_value = b'\xef\xbe\xad\xde'  # Replace with the data to write
    bytes_written = process.write_memory(address, new_value, len(new_value))
    print(f"Wrote {bytes_written} bytes to address {hex(address)}: {new_value}")

    # Get memory protection information
    mem_info = process.get_memory_info(address)
    print(f"Memory protection info at address {hex(address)}: {mem_info}")

    # Change memory protection
    old_protect = process.protect_memory(address, size, MemoryAccess.PAGE_READWRITE)
    print(f"Changed memory protection at address {hex(address)} to PAGE_READWRITE, old protection: {old_protect}")

# The process will automatically detach when exiting the context manager
print(f"Detached from process: {process_name}")
```