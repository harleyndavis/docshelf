import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

# Ensure the secret key is available before settings are first evaluated.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key-not-for-production")

from markdown_viewer import views  # noqa: E402


def _write_md(directory: Path, name: str, content: str) -> Path:
    path = directory / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


class IndexViewNoDocsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        views._render_doc.cache_clear()

    def tearDown(self):
        views._render_doc.cache_clear()
        self.tmpdir.cleanup()

    def test_returns_200_when_docs_dir_is_empty(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_shows_no_documents_found_message_when_docs_dir_is_empty(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertContains(response, "No documents found")


class IndexViewWithDocsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(self.docs_path, "alpha", "# Alpha")
        _write_md(self.docs_path, "beta", "# Beta")
        views._render_doc.cache_clear()

    def tearDown(self):
        views._render_doc.cache_clear()
        self.tmpdir.cleanup()

    def test_each_stem_appears_in_response(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertContains(response, "alpha")
        self.assertContains(response, "beta")

    def test_each_stem_is_an_anchor_linking_to_its_document(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertContains(response, 'href="/docs/alpha/"')
        self.assertContains(response, 'href="/docs/beta/"')

    def test_non_md_files_are_excluded_from_listing(self):
        (self.docs_path / "ignored.txt").write_text("ignored", encoding="utf-8")
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertNotContains(response, "ignored")


class IndexViewSortingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        # Uppercase names sort before lowercase in ASCII order, so these three
        # deliberately exercise the case-insensitive key.
        _write_md(self.docs_path, "Zebra", "# Zebra")
        _write_md(self.docs_path, "apple", "# Apple")
        _write_md(self.docs_path, "Mango", "# Mango")
        views._render_doc.cache_clear()

    def tearDown(self):
        views._render_doc.cache_clear()
        self.tmpdir.cleanup()

    def test_documents_are_listed_case_insensitively_sorted(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        content = response.content.decode()
        pos_apple = content.index("apple")
        pos_mango = content.index("Mango")
        pos_zebra = content.index("Zebra")
        self.assertLess(pos_apple, pos_mango)
        self.assertLess(pos_mango, pos_zebra)


class DocumentViewValidSlugTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(self.docs_path, "my-doc", "# My Document\n\nHello world.")
        views._render_doc.cache_clear()

    def tearDown(self):
        views._render_doc.cache_clear()
        self.tmpdir.cleanup()

    def test_returns_200_for_existing_slug(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/my-doc/")
        self.assertEqual(response.status_code, 200)

    def test_rendered_markdown_heading_appears_in_response(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/my-doc/")
        # The "# My Document" heading should be rendered to an <h1> element.
        self.assertContains(response, "<h1")
        self.assertContains(response, "My Document")

    def test_slug_is_used_as_page_title(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/my-doc/")
        self.assertContains(response, "my-doc")

    def test_markdown_paragraph_renders_as_html_p_element(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/my-doc/")
        self.assertContains(response, "<p>")
        self.assertContains(response, "Hello world.")


class DocumentViewUnknownSlugTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        views._render_doc.cache_clear()

    def tearDown(self):
        views._render_doc.cache_clear()
        self.tmpdir.cleanup()

    def test_returns_404_for_nonexistent_slug(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/does-not-exist/")
        self.assertEqual(response.status_code, 404)


class DocumentViewHtmlSanitizationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(
            self.docs_path,
            "xss-test",
            "<script>alert(1)</script>\n\nSafe content.",
        )
        views._render_doc.cache_clear()

    def tearDown(self):
        views._render_doc.cache_clear()
        self.tmpdir.cleanup()

    def test_script_tag_is_not_present_as_a_live_html_element(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/xss-test/")
        self.assertEqual(response.status_code, 200)
        # The literal <script> opening tag must be absent or escaped in output.
        self.assertNotIn("<script>", response.content.decode())

    def test_safe_content_still_renders_when_script_is_stripped(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/xss-test/")
        self.assertContains(response, "Safe content.")


class RenderDocCachingTest(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        views._render_doc.cache_clear()

    def tearDown(self):
        views._render_doc.cache_clear()
        self.tmpdir.cleanup()

    def test_file_is_read_only_once_for_identical_path_and_mtime(self):
        path = _write_md(self.docs_path, "cached-doc", "# Cache Test")
        path_str = str(path)
        mtime = path.stat().st_mtime

        with patch.object(Path, "read_text", wraps=path.read_text) as mock_read:
            views._render_doc(path_str, mtime)
            views._render_doc(path_str, mtime)

        self.assertEqual(mock_read.call_count, 1)
