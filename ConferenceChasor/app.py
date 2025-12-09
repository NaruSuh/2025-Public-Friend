from __future__ import annotations

import io
import logging
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, render_template, request, send_file

from certgen.config_loader import load_config
from certgen.data_loader import SheetLoader
from certgen.generator import CertificateGenerator

LOGGER = logging.getLogger("certgen.web")

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            return _handle_submission()
        except ValueError as exc:
            LOGGER.warning("Validation error: %s", exc)
            error = str(exc)
        except Exception as exc:  # pragma: no cover - runtime safety
            LOGGER.exception("Unexpected failure while generating certificates")
            error = f"서버 처리 중 오류가 발생했습니다: {exc}"
        return render_template("index.html", error=error)
    return render_template("index.html")


def _handle_submission():
    sheet_file = request.files.get("sheet")
    if not sheet_file or not sheet_file.filename:
        raise ValueError("Google Form 응답 파일을 업로드하세요.")

    config_file = request.files.get("config")
    sheet_name = request.form.get("sheet_name") or None
    limit_raw = (request.form.get("limit") or "").strip()
    limit = None
    if limit_raw:
        if not limit_raw.isdigit() or int(limit_raw) <= 0:
            raise ValueError("Limit 값은 양의 정수여야 합니다.")
        limit = int(limit_raw)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        sheet_path = tmpdir_path / sheet_file.filename
        sheet_file.save(sheet_path)

        config_path = None
        if config_file and config_file.filename:
            config_path = tmpdir_path / config_file.filename
            config_file.save(config_path)

        config = load_config(str(config_path) if config_path else None)
        if sheet_name:
            config.input.sheet_name = sheet_name

        loader = SheetLoader(config)
        participants = loader.load(str(sheet_path))
        if limit:
            participants = participants[:limit]

        if not participants:
            raise ValueError("조건을 만족하는 참가자가 없습니다.")

        generator = CertificateGenerator(config)
        output_dir = tmpdir_path / "output"
        created = generator.build_all(participants, output_dir)

        zip_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_bytes, "w", zipfile.ZIP_DEFLATED) as zipf:
            for pdf_path in created:
                zipf.write(pdf_path, arcname=pdf_path.name)
        zip_bytes.seek(0)

        zip_name = f"{config.event.title.replace(' ', '_')}_certificates.zip"
        return send_file(
            zip_bytes,
            mimetype="application/zip",
            as_attachment=True,
            download_name=zip_name,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=False, host="0.0.0.0", port=8000)
