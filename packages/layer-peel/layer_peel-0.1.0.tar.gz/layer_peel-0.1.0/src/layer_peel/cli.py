#!/usr/bin/env python3
"""
Layer Peel Command Line Interface

Provides a simple and easy-to-use command line tool for recursively extracting nested compressed files.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import extract, __version__
from .types import ExtractConfig
from .utils import lifespan
from .ct import extract_funcs


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        prog="layer_peel",
        description="Recursively extract multi-layer nested compressed files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  layer_peel archive.zip                    # Extract to current directory
  layer_peel archive.zip -o /tmp/output     # Extract to specified directory
  layer_peel archive.zip -d 10              # Set maximum recursion depth to 10
  layer_peel archive.zip --quiet            # Silent mode
        """,
    )

    parser.add_argument("input_file", type=Path, help="Input file path to extract")

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Output directory (default: current directory)",
    )

    parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=5,
        help="Maximum recursion depth (default: 5)",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=65536,
        help="Read chunk size (default: 65536 bytes)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Silent mode, do not show progress information",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose mode, show more information",
    )

    parser.add_argument(
        "--version", action="version", version=f"layer_peel {__version__}"
    )

    return parser


def extract_to_files(
    input_file: Path,
    output_dir: Path,
    depth: int = 5,
    chunk_size: int = 65536,
    quiet: bool = False,
    verbose: bool = False,
) -> None:
    """Save extracted files to disk"""
    if not input_file.exists():
        print(f"Error: Input file '{input_file}' does not exist", file=sys.stderr)
        sys.exit(1)

    if not input_file.is_file():
        print(f"Error: '{input_file}' is not a file", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    if not quiet:
        print(f"Starting extraction: {input_file}")
        print(f"Output directory: {output_dir}")
        print(f"Maximum recursion depth: {depth}")
        print("-" * 50)

    config = ExtractConfig(
        chunk_size=chunk_size,
        lifespan_manager=lifespan,
        extract_funcs=extract_funcs,  # type: ignore[arg-type]
    )

    try:
        with open(input_file, "rb") as f:
            file_count = 0

            for file_data, file_path, mime_type in extract(
                f, str(input_file), depth=depth, config=config
            ):
                file_count += 1

                # Clean file path, remove unsafe characters
                safe_path = file_path.replace("\\", "/")
                if safe_path.startswith("/"):
                    safe_path = safe_path[1:]

                output_file = output_dir / safe_path
                output_file.parent.mkdir(parents=True, exist_ok=True)

                if verbose:
                    print(f"Extracting: {safe_path}")
                    if mime_type:
                        print(f"  Type: {mime_type}")

                # Write file
                with open(output_file, "wb") as out_f:
                    for chunk in file_data:
                        out_f.write(chunk)

                if not quiet and not verbose:
                    print(f"Extracted: {safe_path}")

            if not quiet:
                print("-" * 50)
                print(f"Extraction complete! Processed {file_count} files")

    except KeyboardInterrupt:
        print("\nUser interrupted operation", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main(argv: Optional[list[str]] = None) -> None:
    """Main entry function"""
    parser = create_parser()
    args = parser.parse_args(argv)

    extract_to_files(
        input_file=args.input_file,
        output_dir=args.output,
        depth=args.depth,
        chunk_size=args.chunk_size,
        quiet=args.quiet,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
