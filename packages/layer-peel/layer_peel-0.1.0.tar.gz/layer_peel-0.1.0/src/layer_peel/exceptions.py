"""
Layer Peel Exception Class Definitions

Defines all custom exception classes used in the library, providing better error handling and debugging information.
"""

from typing import Optional


class LayerPeelError(Exception):
    """Base exception class for Layer Peel library"""

    pass


class UnsupportedFormatError(LayerPeelError):
    """Unsupported file format exception"""

    def __init__(self, format_name: str, file_path: str = ""):
        self.format_name = format_name
        self.file_path = file_path
        message = f"Unsupported file format: {format_name}"
        if file_path:
            message += f" (file: {file_path})"
        super().__init__(message)


class ExtractionError(LayerPeelError):
    """Exception during extraction process"""

    def __init__(
        self,
        message: str,
        file_path: str = "",
        original_error: Optional[Exception] = None,
    ):
        self.file_path = file_path
        self.original_error = original_error

        full_message = f"Extraction failed: {message}"
        if file_path:
            full_message += f" (file: {file_path})"
        if original_error:
            full_message += f" (cause: {str(original_error)})"

        super().__init__(full_message)


class CorruptedArchiveError(ExtractionError):
    """Corrupted archive file exception"""

    def __init__(self, file_path: str = "", original_error: Optional[Exception] = None):
        super().__init__(
            "Archive file is corrupted or format is incorrect",
            file_path=file_path,
            original_error=original_error,
        )


class MaxDepthExceededError(LayerPeelError):
    """Maximum recursion depth exceeded exception"""

    def __init__(self, max_depth: int, file_path: str = ""):
        self.max_depth = max_depth
        self.file_path = file_path
        message = f"Maximum recursion depth {max_depth} exceeded"
        if file_path:
            message += f" (file: {file_path})"
        super().__init__(message)


class FileAccessError(LayerPeelError):
    """File access exception"""

    def __init__(
        self,
        file_path: str,
        operation: str = "access",
        original_error: Optional[Exception] = None,
    ):
        self.file_path = file_path
        self.operation = operation
        self.original_error = original_error

        message = f"Cannot {operation} file: {file_path}"
        if original_error:
            message += f" (cause: {str(original_error)})"

        super().__init__(message)


class EncodingError(LayerPeelError):
    """Filename encoding exception"""

    def __init__(
        self, filename_bytes: bytes, original_error: Optional[Exception] = None
    ):
        self.filename_bytes = filename_bytes
        self.original_error = original_error

        message = f"Cannot decode filename: {filename_bytes!r}"
        if original_error:
            message += f" (cause: {str(original_error)})"

        super().__init__(message)
