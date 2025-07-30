from typing import Any, Generator, Iterable, Iterator

from stream_unzip import stream_unzip as _stream_unzip


from ..utils import get_mime_type

DEFAULT_BLOCK_SIZE = 65536


def stream_unzip(
    chunks: Iterable[bytes],
    block_size: int | None = None,
) -> Generator[tuple[bytes, int, Iterator[bytes]], Any, None]:
    """
    A streaming function for extracting zip files.

    zipfile_chunks: Byte data of zip file input in chunks.
    block_size: Block size used by zip file (default 65536 bytes).

    Returns:
        Tuple of (filename, file_size, file_content_generator) for each file.
    """
    for file_name, file_size, unzipped_chunks in _stream_unzip(
        iter(chunks), chunk_size=block_size or DEFAULT_BLOCK_SIZE
    ):
        yield file_name, file_size, unzipped_chunks


def is_zip_file(data: bytes) -> bool:
    mime_type = get_mime_type(data)
    return mime_type == "application/zip"
