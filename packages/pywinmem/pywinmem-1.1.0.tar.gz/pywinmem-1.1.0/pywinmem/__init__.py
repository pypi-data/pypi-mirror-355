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

"""Main package for PyWinMem - Windows memory manipulation toolkit."""
from .winmem import Enumerator, Thread, Module, Process
from .low.winmem_types import ProcessAccess, MemoryAccess

__version__ = "0.1.2"
__all__ = ["Enumerator", "Thread", "Module", "Process", "ProcessAccess", "MemoryAccess"]
