
from __future__ import annotations

import argparse
import io
import logging
import tempfile
import zipfile
from pathlib import Path

from certgen.config_loader import load_config
from certgen.data_loader import SheetLoader
from certgen.generator import CertificateGenerator

LOGGER = logging.getLogger("certgen.web_runner")

def main():
    """
    CLI wrapper to simulate the web interface for certificate generation.
    This script provides the functionality of the web app without needing to run a Flask server,
    which is useful in environments with restricted network permissions.
    """
    parser = argparse.ArgumentParser(description="Generate certificates from a spreadsheet, similar to the web UI.")
    parser.add_argument("--sheet", required=True, help="Path to the Google Form response file (Excel/CSV).")
    parser.add_argument("--config", required=False, help="Path to a custom 'config.yaml' file. If not provided, defaults will be used.")
    parser.add_argument("--sheet_name", required=False, help="Name of the specific sheet to use in the Excel file.")
    parser.add_argument("--limit", type=int, help="Limit the number of certificates to generate (must be a positive integer).")
    parser.add_argument("--output_zip", required=True, help="Path to save the resulting .zip file.")
    args = parser.parse_args()

    try:
        run_generation(args.sheet, args.config, args.sheet_name, args.limit, args.output_zip)
        LOGGER.info(f"성공적으로 인증서 zip 파일을 생성했습니다: {args.output_zip}")
    except ValueError as exc:
        LOGGER.error(f"입력 값 오류: {exc}", exc_info=True)
    except FileNotFoundError as exc:
        LOGGER.error(f"파일을 찾을 수 없음: {exc}", exc_info=True)
    except KeyError as exc:
        LOGGER.error(f"설정 또는 데이터 파일에 필요한 컬럼이 없음: {exc}", exc_info=True)
    except Exception as exc:
        LOGGER.error(f"인증서 생성 중 예기치 않은 오류가 발생했습니다: {exc}", exc_info=True)

def run_generation(sheet_path: str, config_path: str | None, sheet_name: str | None, limit: int | None, output_zip_path: str):
    """Handles the certificate generation logic."""
    if not Path(sheet_path).exists():
        raise FileNotFoundError(f"지정한 시트 파일을 찾을 수 없습니다: {sheet_path}")

    if limit is not None and limit <= 0:
        raise ValueError("Limit 값은 양의 정수여야 합니다.")

    config = load_config(config_path)
    if sheet_name:
        config.input.sheet_name = sheet_name

    loader = SheetLoader(config)
    participants = loader.load(sheet_path)
    if limit:
        participants = participants[:limit]

    if not participants:
        raise ValueError("조건을 만족하는 참가자가 없습니다. 필터 설정을 확인하세요.")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generator = CertificateGenerator(config)
        created_pdfs = generator.build_all(participants, output_dir)

        if not created_pdfs:
            raise RuntimeError("PDF 파일이 하나도 생성되지 않았습니다.")

        zip_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_bytes, "w", zipfile.ZIP_DEFLATED) as zipf:
            for pdf_path in created_pdfs:
                zipf.write(pdf_path, arcname=pdf_path.name)

        with open(output_zip_path, "wb") as f:
            f.write(zip_bytes.getvalue())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
