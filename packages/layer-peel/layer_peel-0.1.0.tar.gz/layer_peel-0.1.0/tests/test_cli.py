"""
测试命令行接口
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from layer_peel.cli import create_parser, extract_to_files, main


class TestCreateParser:
    """测试命令行参数解析器"""

    def test_create_parser_basic(self):
        """测试基本解析器创建"""
        parser = create_parser()

        assert parser.prog == "layer_peel"
        assert (
            parser.description is not None
            and "Recursively extract" in parser.description
        )

    def test_parse_basic_args(self):
        """测试基本参数解析"""
        parser = create_parser()
        args = parser.parse_args(["test.zip"])

        assert args.input_file == Path("test.zip")
        assert args.output == Path.cwd()
        assert args.depth == 5
        assert args.chunk_size == 65536
        assert not args.quiet
        assert not args.verbose

    def test_parse_all_args(self):
        """测试所有参数解析"""
        parser = create_parser()
        args = parser.parse_args(
            [
                "archive.zip",
                "-o",
                "/tmp/output",
                "-d",
                "10",
                "--chunk-size",
                "32768",
                "--quiet",
                "--verbose",
            ]
        )

        assert args.input_file == Path("archive.zip")
        assert args.output == Path("/tmp/output")
        assert args.depth == 10
        assert args.chunk_size == 32768
        assert args.quiet
        assert args.verbose

    def test_parse_version(self):
        """测试版本参数"""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])


class TestExtractToFiles:
    """测试文件解压缩功能"""

    def test_extract_to_files_nonexistent_file(self, capsys):
        """测试不存在的文件"""
        with pytest.raises(SystemExit):
            extract_to_files(
                input_file=Path("nonexistent.zip"), output_dir=Path("/tmp/test")
            )

        captured = capsys.readouterr()
        assert "does not exist" in captured.err

    def test_extract_to_files_directory_input(self, tmp_path, capsys):
        """测试输入是目录的情况"""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        with pytest.raises(SystemExit):
            extract_to_files(input_file=test_dir, output_dir=Path("/tmp/test"))

        captured = capsys.readouterr()
        assert "is not a file" in captured.err

    @patch("layer_peel.cli.extract")
    def test_extract_to_files_success(self, mock_extract, tmp_path):
        """测试成功解压缩"""
        # 创建测试输入文件
        input_file = tmp_path / "test.zip"
        input_file.write_bytes(b"test data")

        # 创建输出目录
        output_dir = tmp_path / "output"

        # 模拟extract函数返回
        mock_extract.return_value = [
            (iter([b"file content"]), "test.txt", "text/plain")
        ]

        # 执行解压缩
        extract_to_files(input_file=input_file, output_dir=output_dir, quiet=True)

        # 验证输出文件
        output_file = output_dir / "test.txt"
        assert output_file.exists()
        assert output_file.read_bytes() == b"file content"

    @patch("layer_peel.cli.extract")
    def test_extract_to_files_with_nested_path(self, mock_extract, tmp_path):
        """测试嵌套路径处理"""
        input_file = tmp_path / "test.zip"
        input_file.write_bytes(b"test data")

        output_dir = tmp_path / "output"

        # 模拟嵌套文件路径
        mock_extract.return_value = [
            (iter([b"content1"]), "archive.zip_/inner/file1.txt", "text/plain"),
            (iter([b"content2"]), "archive.zip_/file2.txt", "text/plain"),
        ]

        extract_to_files(input_file=input_file, output_dir=output_dir, quiet=True)

        # 验证路径清理和文件创建
        file1 = output_dir / "archive.zip_" / "inner" / "file1.txt"
        file2 = output_dir / "archive.zip_" / "file2.txt"

        assert file1.exists()
        assert file2.exists()
        assert file1.read_bytes() == b"content1"
        assert file2.read_bytes() == b"content2"

    @patch("layer_peel.cli.extract")
    def test_extract_to_files_verbose_mode(self, mock_extract, tmp_path, capsys):
        """测试详细模式输出"""
        input_file = tmp_path / "test.zip"
        input_file.write_bytes(b"test data")

        output_dir = tmp_path / "output"

        mock_extract.return_value = [(iter([b"content"]), "test.txt", "text/plain")]

        extract_to_files(input_file=input_file, output_dir=output_dir, verbose=True)

        captured = capsys.readouterr()
        assert "Extracting: test.txt" in captured.out
        assert "Type: text/plain" in captured.out

    @patch("layer_peel.cli.extract")
    def test_extract_to_files_keyboard_interrupt(self, mock_extract, tmp_path, capsys):
        """测试键盘中断处理"""
        input_file = tmp_path / "test.zip"
        input_file.write_bytes(b"test data")

        output_dir = tmp_path / "output"

        mock_extract.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit):
            extract_to_files(input_file=input_file, output_dir=output_dir)

        captured = capsys.readouterr()
        assert "User interrupted operation" in captured.err

    @patch("layer_peel.cli.extract")
    def test_extract_to_files_exception(self, mock_extract, tmp_path, capsys):
        """测试异常处理"""
        input_file = tmp_path / "test.zip"
        input_file.write_bytes(b"test data")

        output_dir = tmp_path / "output"

        mock_extract.side_effect = Exception("Test error")

        with pytest.raises(SystemExit):
            extract_to_files(input_file=input_file, output_dir=output_dir)

        captured = capsys.readouterr()
        assert "Error: Test error" in captured.err


class TestMain:
    """测试主函数"""

    @patch("layer_peel.cli.extract_to_files")
    def test_main_basic(self, mock_extract_to_files):
        """测试基本主函数调用"""
        main(["test.zip"])

        mock_extract_to_files.assert_called_once()
        args = mock_extract_to_files.call_args[1]
        assert args["input_file"] == Path("test.zip")
        assert args["output_dir"] == Path.cwd()
        assert args["depth"] == 5
        assert not args["quiet"]

    @patch("layer_peel.cli.extract_to_files")
    def test_main_with_all_args(self, mock_extract_to_files):
        """测试所有参数的主函数调用"""
        main(
            [
                "archive.zip",
                "-o",
                "/tmp/output",
                "-d",
                "10",
                "--chunk-size",
                "32768",
                "--quiet",
                "--verbose",
            ]
        )

        mock_extract_to_files.assert_called_once()
        args = mock_extract_to_files.call_args[1]
        assert args["input_file"] == Path("archive.zip")
        assert args["output_dir"] == Path("/tmp/output")
        assert args["depth"] == 10
        assert args["chunk_size"] == 32768
        assert args["quiet"]
        assert args["verbose"]
