from typing import (
    Protocol,
    runtime_checkable,
    Callable,
    Iterable,
    Generator,
    Any,
    Iterator,
)
from dataclasses import dataclass


@runtime_checkable
class RawIOBase(Protocol):
    def read(self, size: int | None = -1, /) -> bytes: ...

    def seek(self, pos: int, whence: int = 0, /) -> int: ...


def _default_format_path(x: str) -> str:
    return f"{x}!"


@dataclass
class ExtractConfig:
    lifespan_manager: Callable
    extract_funcs: dict[
        Callable[[bytes], bool],
        Callable[
            [Iterable[bytes], int | None],
            Generator[tuple[bytes, int, Iterator[bytes]], Any, None],
        ],
    ]
    chunk_size: int = 65536
    format_path: Callable[[str], str] = _default_format_path
