from io import BytesIO
from typing import Any, Generator, Iterable, Iterator

import rarfile

from ..utils import get_mime_type

DEFAULT_BLOCK_SIZE = 65536


def large_iterator_to_io(iterator):
    buffer = BytesIO()
    for chunk in iterator:
        buffer.write(chunk)
    buffer.seek(0)
    return buffer


def stream_unrar(
    chunks: Iterable[bytes],
    block_size: int | None = None,
) -> Generator[tuple[bytes, int, Iterator[bytes]], Any, None]:
    with rarfile.RarFile(large_iterator_to_io(chunks)) as rf:
        for member in rf.infolist():
            with rf.open(member) as source:
                yield (
                    member.filename,
                    member.file_size,
                    iter(lambda: source.read(block_size or 1024), b""),
                )


def is_rar_file(data: bytes) -> bool:
    mime_type = get_mime_type(data)
    print(mime_type)
    return mime_type == "application/x-rar"
