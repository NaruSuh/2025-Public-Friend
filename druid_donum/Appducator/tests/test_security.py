"""Security tests for HTML sanitization."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_utils import sanitize_html


class TestXSSPrevention:
    """Test XSS attack vector prevention."""

    def test_blocks_script_tags(self):
        """Script tags should be completely stripped."""
        malicious = '<script>alert("XSS")</script><p>Safe content</p>'
        result = sanitize_html(malicious)
        assert '<script>' not in result
        # bleach strips tags but may leave content
        assert 'Safe content' in result

    def test_blocks_javascript_protocol(self):
        """javascript: protocol in href should be blocked."""
        malicious = '<a href="javascript:alert(1)">Click me</a>'
        result = sanitize_html(malicious)
        assert 'javascript:' not in result

    def test_blocks_onerror_attribute(self):
        """Event handler attributes should be stripped."""
        malicious = '<img src=x onerror="alert(1)">'
        result = sanitize_html(malicious)
        assert 'onerror' not in result
        assert 'alert' not in result

    def test_allows_safe_html(self):
        """Safe HTML should pass through unchanged."""
        safe = '<p>Hello <strong>world</strong>!</p>'
        result = sanitize_html(safe)
        assert '<p>' in result
        assert '<strong>' in result
        assert 'Hello' in result
        assert 'world' in result

    def test_blocks_data_uri(self):
        """data: URIs should be blocked to prevent embedded scripts."""
        malicious = '<a href="data:text/html,<script>alert(1)</script>">Click</a>'
        result = sanitize_html(malicious)
        # bleach should strip the dangerous href
        assert 'data:text/html' not in result or '<a' not in result

    @pytest.mark.parametrize("tag", ["iframe", "object", "embed", "form", "input"])
    def test_blocks_dangerous_tags(self, tag):
        """Dangerous HTML tags should be stripped."""
        malicious = f'<{tag}>content</{tag}>'
        result = sanitize_html(malicious)
        assert f'<{tag}>' not in result

    def test_blocks_onclick_attribute(self):
        """onclick event handlers should be stripped."""
        malicious = '<button onclick="alert(1)">Click</button>'
        result = sanitize_html(malicious)
        assert 'onclick' not in result
        assert 'alert' not in result

    def test_blocks_style_with_javascript(self):
        """style attributes with javascript should be blocked."""
        malicious = '<div style="background:url(javascript:alert(1))">test</div>'
        result = sanitize_html(malicious)
        assert 'javascript:' not in result

    def test_preserves_glossary_spans(self):
        """Glossary highlight spans should be preserved."""
        glossary_html = '<span class="gloss-term" data-term="api" data-tooltip="Application Programming Interface">API</span>'
        result = sanitize_html(glossary_html)
        assert 'gloss-term' in result
        assert 'data-term' in result
        assert 'data-tooltip' in result
        assert 'API' in result

    def test_allows_safe_links(self):
        """Safe HTTP/HTTPS links should be allowed."""
        safe_link = '<a href="https://example.com" title="Example">Link</a>'
        result = sanitize_html(safe_link)
        assert 'https://example.com' in result
        assert 'Example' in result

    def test_blocks_vbscript_protocol(self):
        """vbscript: protocol should be blocked."""
        malicious = '<a href="vbscript:msgbox(1)">Click</a>'
        result = sanitize_html(malicious)
        assert 'vbscript:' not in result

    def test_nested_script_tags(self):
        """Nested script tags should be fully stripped."""
        malicious = '<div><script><script>alert(1)</script></script></div>'
        result = sanitize_html(malicious)
        assert '<script>' not in result
        # bleach removes tags but leaves text content

    def test_svg_with_script(self):
        """SVG tags with embedded scripts should be blocked."""
        malicious = '<svg><script>alert(1)</script></svg>'
        result = sanitize_html(malicious)
        assert '<script>' not in result
        assert '<svg>' not in result  # SVG tag also stripped

    def test_html_entity_encoded_script(self):
        """HTML entity encoded scripts should not bypass sanitization."""
        malicious = '&lt;script&gt;alert(1)&lt;/script&gt;'
        result = sanitize_html(malicious)
        # Should remain encoded or be stripped
        assert 'alert(1)' not in result or '&lt;' in result

    def test_allows_code_blocks(self):
        """Code and pre tags should be allowed for syntax highlighting."""
        code_html = '<pre><code class="python">print("hello")</code></pre>'
        result = sanitize_html(code_html)
        assert '<pre>' in result
        assert 'code' in result  # Tag is preserved
        assert 'print' in result

    def test_allows_tables(self):
        """Table elements should be allowed."""
        table_html = '<table><thead><tr><th>Header</th></tr></thead><tbody><tr><td>Data</td></tr></tbody></table>'
        result = sanitize_html(table_html)
        assert '<table>' in result
        assert '<thead>' in result
        assert '<tbody>' in result
        assert '<tr>' in result
        assert '<th>' in result
        assert '<td>' in result
