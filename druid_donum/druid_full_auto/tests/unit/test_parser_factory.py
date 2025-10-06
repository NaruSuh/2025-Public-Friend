"""Smoke tests for parser factory dynamic plugin loading."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.parser_factory import ParserFactory
from src.core.base_crawler import BaseCrawler


def test_parser_factory_loads_dynamic_plugin(tmp_path, monkeypatch):
    temp_root = tmp_path / "temp_plugins"
    plugin_dir = temp_root / "src" / "plugins" / "sample_site"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # make plugin package files
    (plugin_dir / "__init__.py").write_text("", encoding="utf-8")
    (temp_root / "src" / "plugins" / "__init__.py").write_text("", encoding="utf-8")

    crawler_code = textwrap.dedent(
        """
        from src.core.base_crawler import BaseCrawler

        class SampleCrawler(BaseCrawler):
            def fetch_page(self, url: str, params):
                return None

            def parse_list(self, soup):
                return []

            def parse_detail(self, soup, item):
                return item

            def build_params(self, page: int, start_date=None, end_date=None):
                return {"pageIndex": page}
        """
    )
    (plugin_dir / "crawler.py").write_text(crawler_code, encoding="utf-8")

    # Prepend temp root so namespace package merges with project src
    monkeypatch.syspath_prepend(str(temp_root))

    factory = ParserFactory(plugins_dir=str(plugin_dir.parent))
    plugins = factory.list_available_plugins()
    assert "sample_site" in plugins

    crawler = factory.create_crawler("sample_site")
    assert isinstance(crawler, BaseCrawler)
    assert crawler.build_params(3)["pageIndex"] == 3
