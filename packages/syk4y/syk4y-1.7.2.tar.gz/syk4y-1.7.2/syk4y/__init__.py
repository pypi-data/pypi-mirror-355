from .printer import inspect
from .compress import fast_compress, fast_decompress, zip, unzip, to_zip, to_lz4
from .rclone import install_rclone, rclone_get_remotes, rclone_copy


__all__ = [
    "inspect",
    "fast_compress",
    "fast_decompress",
    "zip",
    "unzip",
    "to_zip",
    "to_lz4",
    "install_rclone",
    "rclone_get_remotes",
    "rclone_copy"
]