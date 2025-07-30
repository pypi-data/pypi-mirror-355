import tarfile
from typing import Generator, Any, Iterable, Iterator

DEFAULT_BLOCK_SIZE = 65536


class GeneratorReader:
    def __init__(self, generator: Generator[bytes, None, None]):
        self.generator = generator
        self.buffer = b""

    def read(self, size: int = -1) -> bytes:
        while size < 0 or len(self.buffer) < size:
            try:
                self.buffer += next(self.generator)
            except StopIteration:
                break
        if size < 0:
            result, self.buffer = self.buffer, b""
        else:
            result, self.buffer = self.buffer[:size], self.buffer[size:]
        return result


def stream_untar(
    chunks: Iterable[bytes],
    block_size: int | None = None,
) -> Generator[tuple[bytes, int, Iterator[bytes]], Any, None]:
    with tarfile.open(
        fileobj=GeneratorReader(iter(chunks)),  # type: ignore
        mode="r|*",
        bufsize=block_size or DEFAULT_BLOCK_SIZE,
    ) as tar:
        while True:
            member = tar.next()
            if member is None:
                break
            if member.isfile():
                file_obj = tar.extractfile(member)
                if file_obj is not None:
                    yield (
                        member.name.encode(),
                        member.size,
                        iter(lambda: file_obj.read(block_size), b""),
                    )


def is_tar_file(data: bytes) -> bool:
    if len(data) < 265:
        return False
    return data[257:265] == b"ustar  \x00"
