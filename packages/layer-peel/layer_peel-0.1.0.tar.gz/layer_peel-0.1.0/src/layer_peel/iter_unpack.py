"""
Layer Peel core extraction module

Provides core functionality for recursively extracting multi-layer nested compressed files.
Supports automatic recognition and extraction of various formats including ZIP, TAR, 7Z, RAR, etc.
"""

from typing import Iterator, Callable, Any, Generator, Iterable, Optional, Union
import logging

from .utils import (
    fill_stream,
    read_stream,
    fix_encoding,
    get_mime_type,
    RawIOBase,
    lifespan,
)
from .types import ExtractConfig
from .exceptions import ExtractionError


# Setup logging
logger = logging.getLogger(__name__)

# Default configuration - will be set after import to avoid circular imports
_default_config: Optional[ExtractConfig] = None


def _get_default_config() -> ExtractConfig:
    """Get or create default configuration"""
    global _default_config
    if _default_config is None:
        from .ct import extract_funcs

        _default_config = ExtractConfig(
            chunk_size=65536,
            lifespan_manager=lifespan,
            extract_funcs=extract_funcs,  # type: ignore[arg-type]
        )
    return _default_config


def _extract(
    data: Union[Iterator[bytes], RawIOBase],
    source_path: str,
    extract_func: Callable[
        [Iterable[bytes], Optional[int]],
        Generator[tuple[bytes, int, Iterator[bytes]], Any, None],
    ],
    depth: int,
    config: ExtractConfig,
) -> Generator[tuple[Iterator[bytes], str, Optional[str]], Any, None]:
    """
    Internal extraction function that handles specific format compressed files

    Args:
        data: Input data stream or file object
        extract_func: Extraction function
        source_path: Source file path
        depth: Remaining recursion depth

    Yields:
        tuple[Iterator[bytes], str, Optional[str]]: File data stream, path and MIME type

    Raises:
        ExtractionError: Error occurred during extraction
    """
    try:
        with config.lifespan_manager(source_path):
            data_stream = read_stream(data) if isinstance(data, RawIOBase) else data

            for file_name, file_size, file_body in extract_func(data_stream, None):
                try:
                    decoded_name = fix_encoding(file_name)
                    new_path = f"{source_path}/{decoded_name}"

                    yield from extract(
                        file_body,
                        new_path,
                        depth,
                        config,
                    )
                except Exception as e:
                    logger.warning(f"Skipping corrupted file {source_path}: {e}")
                    continue

    except Exception as e:
        raise ExtractionError(
            "Extraction failed", file_path=source_path, original_error=e
        ) from e


def extract(
    data: Union[Iterator[bytes], RawIOBase],
    source_path: str,
    depth: int = 5,
    config: Optional[ExtractConfig] = None,
) -> Generator[tuple[Iterator[bytes], str, Optional[str]], Any, None]:
    """
    Recursively extract multi-layer nested compressed files

    This is the main API function of the library, capable of automatically recognizing
    compressed file formats and performing recursive extraction.
    Supported formats include: ZIP, TAR, TGZ, 7Z, RAR, etc.

    Args:
        data: Input data, can be byte stream iterator or file object
        source_path: Source file path, used for identification and logging
        depth: Maximum recursion depth to prevent infinite recursion, default 5 layers
        config: ExtractConfig object for configuration. If None, uses default configuration.

    Yields:
        tuple[Iterator[bytes], str, Optional[str]]:
            - Iterator[bytes]: Byte stream of file content
            - str: File path
            - Optional[str]: MIME type of the file (if detectable)

    Raises:
        ExtractionError: Error occurred during extraction

    Example:
        >>> with open('nested.zip', 'rb') as f:
        ...     for file_data, file_path, mime_type in extract(f, 'nested.zip'):
        ...         print(f"Extracted file: {file_path}")
        ...         # Process file data...
    """
    # Use default config if none provided
    if config is None:
        config = _get_default_config()

    temp_chunk = b""
    file_type = None

    # Convert input data to byte stream
    if isinstance(data, RawIOBase):
        data_stream = read_stream(data)
    else:
        data_stream = data

    # Read enough data to detect file type
    try:
        for chunk in data_stream:
            temp_chunk += chunk
            if len(temp_chunk) >= config.chunk_size:
                # Rebuild complete data stream
                iter_data = fill_stream(data_stream, temp_chunk)
                break
        else:
            # Case where data is less than one chunk
            iter_data = fill_stream(fill=temp_chunk)
    except Exception as e:
        raise ExtractionError(
            "Failed to read data", file_path=source_path, original_error=e
        ) from e

    # Detect file type
    if temp_chunk:
        try:
            file_type = get_mime_type(temp_chunk)
            logger.debug(f"Detected file type: {file_type} for {source_path}")
        except Exception as e:
            logger.warning(f"Unable to detect file type {source_path}: {e}")

    # If maximum depth reached, return file directly
    if depth <= 0:
        if iter_data is not None:
            yield iter_data, source_path, file_type
        return

    # Try various extractors
    if iter_data is not None:
        for is_format_func, extract_func in config.extract_funcs.items():
            try:
                if is_format_func(temp_chunk):
                    logger.debug(f"Processing {source_path} with extractor")
                    yield from _extract(
                        iter_data,
                        config.format_path(source_path),
                        extract_func,
                        depth - 1,
                        config,
                    )
                    return
            except Exception as e:
                logger.warning(f"Extractor failed for {source_path}: {e}")
                continue

    # If no matching extractor, return original file
    if iter_data is not None:
        yield iter_data, source_path, file_type
