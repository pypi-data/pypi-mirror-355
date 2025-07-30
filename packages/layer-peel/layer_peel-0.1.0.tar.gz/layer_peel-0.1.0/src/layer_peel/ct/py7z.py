import io
from typing import Generator, Iterable, Iterator, Any


from py7zr import properties, SevenZipFile, exceptions


def iterable_to_bytesio(iterable):
    bytes_io = io.BytesIO()
    for chunk in iterable:
        bytes_io.write(chunk)
    bytes_io.seek(0)
    return bytes_io


class DecompressFile(io.IOBase):
    def __init__(self, zipf, zi):
        self.fp = zipf.fp
        self.src_end = (
            zipf.afterheader + zipf.header.main_streams.packinfo.packpositions[-1]
        )
        self.out_remaining = zi.uncompressed
        self.decompressor = zi.folder.get_decompressor(
            zi.compressed, zi.compressed is not None
        )

    def read(self, size):
        m = min(self.out_remaining, properties.get_memory_limit(), size)
        tmp = self.decompressor.decompress(self.fp, m)
        self.out_remaining -= len(tmp)
        if self.fp.tell() >= self.src_end:
            if self.decompressor.crc is not None and not self.decompressor.check_crc():
                raise exceptions.CrcError(
                    self.decompressor.crc, self.decompressor.digest, None
                )
        return tmp


def is_7z_file(data: bytes) -> bool:
    return data[:6] == b"7z\xbc\xaf\x27\x1c"


def stream_un7z(
    chunks: Iterable[bytes],
    block_size: int | None = None,
) -> Generator[tuple[bytes, int, Iterator[bytes]], Any, None]:
    with SevenZipFile(
        iterable_to_bytesio(iter(chunks)),  # type: ignore
        mode="r",
        blocksize=block_size,
    ) as archive:
        for zi in archive.files:
            if not zi.is_directory and zi.uncompressed and len(zi.uncompressed) > 0:
                d = DecompressFile(archive, zi)
                file_size = (
                    sum(zi.uncompressed)
                    if isinstance(zi.uncompressed, list)
                    else zi.uncompressed
                )
                yield (
                    zi.filename.encode(),
                    file_size,
                    iter(lambda: d.read(block_size or 65536), b""),
                )
