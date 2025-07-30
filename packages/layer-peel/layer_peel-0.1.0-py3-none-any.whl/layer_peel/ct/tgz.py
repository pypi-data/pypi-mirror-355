from typing import Generator, Any, Iterable, Iterator

from .tar import stream_untar

DEFAULT_BLOCK_SIZE = 65536


def stream_untgz(
    chunks: Iterable[bytes],
    block_size: int | None = None,
) -> Generator[tuple[bytes, int, Iterator[bytes]], Any, None]:
    """
    A streaming function for extracting tgz files.

    tgzfile_chunks: Byte data of tgz file input in chunks.
    block_size: Block size used by tar format (default 512 bytes).

    Returns:
        Tuple of (filename, file_size, file_content_generator) for each file.
    """

    return stream_untar(chunks=chunks, block_size=block_size)


def is_tgz_file(data: bytes) -> bool:
    return data[:3] == b"\x1f\x8b\x08"
