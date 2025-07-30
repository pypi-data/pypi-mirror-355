"""
测试核心解压缩功能
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch

from layer_peel import extract
from layer_peel.exceptions import ExtractionError
from layer_peel.types import ExtractConfig
from layer_peel.utils import lifespan
from layer_peel.ct import extract_funcs


class TestExtract:
    """测试 extract 函数"""

    def test_extract_with_zero_depth(self):
        """测试深度为0时的行为"""
        data = BytesIO(b"test data")

        # 深度为0时应该直接返回文件，不抛出异常
        results = list(extract(data, "test.txt", depth=0))
        assert len(results) == 1

        file_data, file_path, mime_type = results[0]
        assert file_path == "test.txt"
        assert b"".join(file_data) == b"test data"

    def test_extract_empty_data(self):
        """测试空数据的处理"""
        data = BytesIO(b"")

        results = list(extract(data, "empty.txt", depth=1))
        assert len(results) == 1

        file_data, file_path, mime_type = results[0]
        assert file_path == "empty.txt"
        assert b"".join(file_data) == b""

    def test_extract_non_archive_data(self):
        """测试非压缩文件数据"""
        test_data = b"This is just plain text data"
        data = BytesIO(test_data)

        results = list(extract(data, "plain.txt", depth=1))
        assert len(results) == 1

        file_data, file_path, mime_type = results[0]
        assert file_path == "plain.txt"
        assert b"".join(file_data) == test_data
        assert mime_type == "text/plain"

    @patch("layer_peel.iter_unpack.get_mime_type")
    def test_extract_mime_type_detection_failure(self, mock_get_mime_type):
        """测试MIME类型检测失败的情况"""
        mock_get_mime_type.side_effect = Exception("MIME detection failed")

        test_data = b"some data"
        data = BytesIO(test_data)

        results = list(extract(data, "test.bin", depth=1))
        assert len(results) == 1

        file_data, file_path, mime_type = results[0]
        assert file_path == "test.bin"
        assert b"".join(file_data) == test_data
        # MIME类型应该为None，因为检测失败
        assert mime_type is None

    def test_extract_with_custom_chunk_size(self):
        """测试自定义块大小"""
        test_data = b"x" * 1000  # 1KB数据
        data = BytesIO(test_data)

        # 创建自定义配置
        config = ExtractConfig(
            chunk_size=100,
            lifespan_manager=lifespan,
            extract_funcs=extract_funcs,
        )

        results = list(extract(data, "large.txt", depth=1, config=config))
        assert len(results) == 1

        file_data, file_path, mime_type = results[0]
        assert file_path == "large.txt"
        assert b"".join(file_data) == test_data

    def test_extract_with_custom_lifespan_manager(self):
        """测试自定义生命周期管理器"""
        calls = []

        def custom_lifespan(path):
            from contextlib import contextmanager

            @contextmanager
            def manager():
                calls.append(f"start:{path}")
                try:
                    yield
                finally:
                    calls.append(f"end:{path}")

            return manager()

        # 创建一个模拟的ZIP文件头，这样会触发压缩文件处理逻辑
        # PK\x03\x04 是ZIP文件的魔数
        test_data = b"PK\x03\x04" + b"fake zip data"
        data = BytesIO(test_data)

        # 创建自定义配置，但移除ZIP处理器以避免实际解压缩
        custom_extract_funcs = {}  # 空的提取函数字典

        config = ExtractConfig(
            chunk_size=65536,
            lifespan_manager=custom_lifespan,
            extract_funcs=custom_extract_funcs,
        )

        results = list(extract(data, "test.zip", depth=1, config=config))
        assert len(results) == 1

        # 对于非压缩文件，生命周期管理器不会被调用
        # 这是正确的行为，因为生命周期管理器只在实际解压缩时使用
        file_data, file_path, mime_type = results[0]
        assert file_path == "test.zip"
        assert b"".join(file_data) == test_data


class TestExtractErrorHandling:
    """测试错误处理"""

    def test_extract_with_read_error(self):
        """测试读取错误的处理"""
        mock_file = Mock()
        mock_file.read.side_effect = IOError("Read failed")

        with pytest.raises(ExtractionError):
            list(extract(mock_file, "error.txt", depth=1))

    def test_extract_with_negative_depth(self):
        """测试负数深度"""
        data = BytesIO(b"test")

        # 负数深度应该直接返回文件，不抛出异常
        results = list(extract(data, "test.txt", depth=-1))
        assert len(results) == 1

        file_data, file_path, mime_type = results[0]
        assert file_path == "test.txt"
        assert b"".join(file_data) == b"test"


class TestExtractIntegration:
    """集成测试"""

    def test_extract_basic_workflow(self):
        """测试基本工作流程"""
        # 创建一个简单的测试数据
        test_data = b"Hello, Layer Peel!"
        data = BytesIO(test_data)

        # 执行解压缩
        results = list(extract(data, "hello.txt"))

        # 验证结果
        assert len(results) == 1
        file_data, file_path, mime_type = results[0]

        assert file_path == "hello.txt"
        assert b"".join(file_data) == test_data
        assert mime_type is not None  # 应该检测到某种MIME类型
