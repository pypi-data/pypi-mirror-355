import sys
import mmap
import ctypes
from typing import Callable, Generic, Type, TypeVar

from hydrosim_sdk.hydrosim_structs import HydroSimStructure

T = TypeVar("T")


class HydroSimFile(Generic[T]):
    file_name = None
    mmap_file = None
    struct_type: Callable[[HydroSimStructure], T] = None
    data: T

    def __init__(
        self,
        struct_type: Callable[[HydroSimStructure], T],
        file_name: str,
        extra_name: str,
    ):
        self.struct_type = struct_type
        self.file_name = file_name
        if extra_name:
            self.file_name += f".{extra_name}"
        self.data = struct_type()

    def update(self):
        if not self.mmap_file:
            print(f"Connecting to memory mapped file: {self.file_name}")
            if sys.platform == "win32":
                self.mmap_file = mmap.mmap(
                    -1,
                    ctypes.sizeof(self.struct_type),
                    self.file_name,
                    access=mmap.ACCESS_WRITE,
                )
            else:
                with open(self.file_name, "rb") as f:
                    self.mmap_file = mmap.mmap(
                        f.fileno(),
                        ctypes.sizeof(self.struct_type),
                        prot=mmap.PROT_READ,
                    )
        self.data = self.struct_type.from_buffer_copy(self.mmap_file)

    def stop(self):
        self.mmap_file.close()
