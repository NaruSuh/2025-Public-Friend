from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from .config_loader import AppConfig, load_config
from .data_loader import SheetLoader
from .generator import CertificateGenerator


LOGGER = logging.getLogger("certgen")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="certgen",
        description="Generate conference certificates from a spreadsheet",
    )
    parser.add_argument("sheet", help="Path to Excel or CSV file exported from Google Form")
    parser.add_argument(
        "--config",
        "-c",
        dest="config",
        help="Path to YAML config (see config.example.yaml)",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        default=None,
        help="Directory for generated PDFs (default: config output.dirname)",
    )
    parser.add_argument(
        "--sheet-name",
        dest="sheet_name",
        default=None,
        help="Excel sheet name to read (overrides config)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Generate only the first N rows (useful for tests)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    config = load_config(args.config)
    if args.sheet_name:
        config.input.sheet_name = args.sheet_name

    loader = SheetLoader(config)
    participants = loader.load(args.sheet)
    if args.limit:
        participants = participants[: args.limit]

    if not participants:
        LOGGER.warning("No participants matched the criteria.")
        return 1

    output_dir = Path(args.output or config.output.dirname)
    generator = CertificateGenerator(config)
    created = generator.build_all(participants, output_dir)

    LOGGER.info("Generated %s certificates into %s", len(created), output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
