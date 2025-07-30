"""
测试工具函数
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch

from layer_peel.utils import (
    read_stream,
    get_mime_type,
    get_extension,
    file_to_bytesio,
    fill_stream,
    fix_encoding,
    lifespan,
)
from layer_peel.exceptions import FileAccessError, EncodingError


class TestReadStream:
    """测试 read_stream 函数"""

    def test_read_stream_basic(self):
        """测试基本读取功能"""
        data = b"Hello, World!"
        file_obj = BytesIO(data)

        chunks = list(read_stream(file_obj, size=5))
        result = b"".join(chunks)

        assert result == data
        assert len(chunks) >= 1  # 至少有一个块

    def test_read_stream_empty_file(self):
        """测试空文件读取"""
        file_obj = BytesIO(b"")

        chunks = list(read_stream(file_obj))

        assert chunks == []

    def test_read_stream_large_data(self):
        """测试大数据读取"""
        data = b"x" * 100000  # 100KB数据
        file_obj = BytesIO(data)

        chunks = list(read_stream(file_obj, size=1024))
        result = b"".join(chunks)

        assert result == data
        assert len(chunks) > 1  # 应该分成多个块

    def test_read_stream_with_error(self):
        """测试读取错误处理"""
        mock_file = Mock()
        mock_file.read.side_effect = IOError("Read failed")
        mock_file.name = "test.txt"

        with pytest.raises(FileAccessError):
            list(read_stream(mock_file))


class TestGetMimeType:
    """测试 get_mime_type 函数"""

    def test_get_mime_type_text(self):
        """测试文本文件类型检测"""
        data = b"Hello, this is plain text"
        mime_type = get_mime_type(data)

        assert "text" in mime_type.lower()

    def test_get_mime_type_empty_data(self):
        """测试空数据的MIME类型"""
        mime_type = get_mime_type(b"")

        assert mime_type == "application/octet-stream"

    @patch("layer_peel.utils.MAGIC_AVAILABLE", True)
    @patch("layer_peel.utils.magic")
    def test_get_mime_type_with_error(self, mock_magic):
        """测试MIME检测错误处理"""
        mock_magic.Magic.return_value.from_buffer.side_effect = Exception(
            "Magic failed"
        )

        mime_type = get_mime_type(b"some data")

        assert mime_type == "application/octet-stream"

    @patch("layer_peel.utils.MAGIC_AVAILABLE", False)
    def test_get_mime_type_fallback(self):
        """测试MIME检测回退机制"""
        # 测试ZIP文件签名
        zip_data = b"PK\x03\x04" + b"\x00" * 100
        mime_type = get_mime_type(zip_data)
        assert mime_type == "application/zip"

        # 测试未知数据
        unknown_data = b"unknown data"
        mime_type = get_mime_type(unknown_data)
        assert mime_type == "application/octet-stream"


class TestGetExtension:
    """测试 get_extension 函数"""

    def test_get_extension_zip(self):
        """测试ZIP文件扩展名"""
        ext = get_extension("application/zip")
        assert ext == ".zip"

    def test_get_extension_text(self):
        """测试文本文件扩展名"""
        ext = get_extension("text/plain")
        assert ext == ".txt"

    def test_get_extension_unknown(self):
        """测试未知MIME类型"""
        ext = get_extension("unknown/type")
        assert ext is None


class TestFileToByteIO:
    """测试 file_to_bytesio 函数"""

    def test_file_to_bytesio_basic(self):
        """测试基本转换功能"""
        data = b"Test data for BytesIO conversion"
        file_obj = BytesIO(data)

        result = file_to_bytesio(file_obj)

        assert isinstance(result, BytesIO)
        assert result.read() == data

    def test_file_to_bytesio_with_error(self):
        """测试转换错误处理"""
        mock_file = Mock()
        mock_file.read.side_effect = IOError("Read failed")
        mock_file.name = "test.txt"

        with pytest.raises(FileAccessError):
            file_to_bytesio(mock_file)


class TestFillStream:
    """测试 fill_stream 函数"""

    def test_fill_stream_with_fill_only(self):
        """测试只有填充数据"""
        fill_data = b"header"

        result = list(fill_stream(fill=fill_data))

        assert result == [fill_data]

    def test_fill_stream_with_data_only(self):
        """测试只有数据流"""
        data_stream = iter([b"chunk1", b"chunk2"])

        result = list(fill_stream(data=data_stream))

        assert result == [b"chunk1", b"chunk2"]

    def test_fill_stream_with_both(self):
        """测试填充数据和数据流"""
        fill_data = b"header"
        data_stream = iter([b"chunk1", b"chunk2"])

        result = list(fill_stream(data=data_stream, fill=fill_data))

        assert result == [b"header", b"chunk1", b"chunk2"]

    def test_fill_stream_with_none(self):
        """测试空参数"""
        result = list(fill_stream())

        assert result == []

    def test_fill_stream_with_error(self):
        """测试数据流错误"""

        def error_generator():
            yield b"chunk1"
            raise Exception("Stream error")

        # 应该产生第一个块，然后记录错误但不抛出异常
        result = list(fill_stream(data=error_generator()))

        assert result == [b"chunk1"]


class TestFixEncoding:
    """测试 fix_encoding 函数"""

    def test_fix_encoding_utf8(self):
        """测试UTF-8编码"""
        utf8_bytes = "中文测试.txt".encode("utf-8")

        result = fix_encoding(utf8_bytes)

        assert result == "中文测试.txt"

    def test_fix_encoding_gbk(self):
        """测试GBK编码"""
        gbk_bytes = "中文测试.txt".encode("gbk")

        result = fix_encoding(gbk_bytes)

        assert result == "中文测试.txt"

    def test_fix_encoding_empty(self):
        """测试空字节"""
        result = fix_encoding(b"")

        assert result == ""

    def test_fix_encoding_ascii(self):
        """测试ASCII编码"""
        ascii_bytes = b"test.txt"

        result = fix_encoding(ascii_bytes)

        assert result == "test.txt"

    def test_fix_encoding_invalid_bytes(self):
        """测试无效字节序列"""
        invalid_bytes = b"\xff\xfe\x00\x01"

        result = fix_encoding(invalid_bytes)

        # 应该返回某种形式的结果，不抛出异常
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("layer_peel.utils.chardet.detect")
    def test_fix_encoding_with_chardet_error(self, mock_detect):
        """测试chardet检测错误"""
        mock_detect.side_effect = Exception("Chardet failed")

        with pytest.raises(EncodingError):
            fix_encoding(b"test")


class TestLifespan:
    """测试 lifespan 上下文管理器"""

    def test_lifespan_normal(self):
        """测试正常使用"""
        with lifespan("test.txt"):
            pass  # 应该正常执行

    def test_lifespan_with_exception(self):
        """测试异常情况"""
        with pytest.raises(ValueError):
            with lifespan("test.txt"):
                raise ValueError("Test error")
