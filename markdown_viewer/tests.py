import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import Client, SimpleTestCase, override_settings

# Ensure the secret key is available before settings are first evaluated.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key-not-for-production")

from markdown_viewer import views  # noqa: E402


def _write_md(directory: Path, name: str, content: str) -> Path:
    path = directory / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


def _clear_caches():
    views._render_doc.cache_clear()
    views._load_meta.cache_clear()


class IndexViewNoDocsTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_returns_200_when_docs_dir_is_empty(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_shows_no_documents_found_message_when_docs_dir_is_empty(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertContains(response, "No documents found")


class IndexViewWithDocsTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(self.docs_path, "alpha", "# Alpha")
        _write_md(self.docs_path, "beta", "# Beta")
        _clear_caches()

    def tearDown(self):
        _clear_caches()
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


class IndexViewSortingTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        # Uppercase names sort before lowercase in ASCII order, so these three
        # deliberately exercise the case-insensitive key.
        _write_md(self.docs_path, "Zebra", "# Zebra")
        _write_md(self.docs_path, "apple", "# Apple")
        _write_md(self.docs_path, "Mango", "# Mango")
        _clear_caches()

    def tearDown(self):
        _clear_caches()
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


class DocumentViewValidSlugTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(self.docs_path, "my-doc", "# My Document\n\nHello world.")
        _clear_caches()

    def tearDown(self):
        _clear_caches()
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


class DocumentViewUnknownSlugTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_returns_404_for_nonexistent_slug(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/does-not-exist/")
        self.assertEqual(response.status_code, 404)


class DocumentViewHtmlSanitizationTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(
            self.docs_path,
            "xss-test",
            "<script>alert(1)</script>\n\nSafe content.",
        )
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_script_tag_is_not_present_as_a_live_html_element(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/xss-test/")
        self.assertEqual(response.status_code, 200)
        # The injected payload must not appear as executable HTML.
        self.assertNotIn("<script>alert(1)</script>", response.content.decode())

    def test_safe_content_still_renders_when_script_is_stripped(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/xss-test/")
        self.assertContains(response, "Safe content.")


class DocumentViewContextTest(SimpleTestCase):
    """Verify the extra context variables added to the document view."""

    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(self.docs_path, "alpha", "# Alpha")
        _write_md(self.docs_path, "beta", "# Beta")
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_documents_context_lists_all_doc_slugs(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/alpha/")
        self.assertEqual(response.status_code, 200)
        # Both slugs should appear in the sidebar rendered by the base template.
        self.assertContains(response, "alpha")
        self.assertContains(response, "beta")

    def test_current_doc_context_marks_active_link(self):
        # The base template adds class "is-active" to the <a> sidebar link
        # whose slug matches current_doc.  The rendered HTML looks like:
        #   <a class="mv-sidebar-link is-active"\n     href="/docs/alpha/">
        # Search for the HTML attribute pattern (not the CSS rule) by looking
        # for the substring that can only appear inside an HTML tag.
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/alpha/")
        content = response.content.decode()
        alpha_link = 'href="/docs/alpha/"'
        beta_link = 'href="/docs/beta/"'
        self.assertIn(alpha_link, content)
        # "mv-sidebar-link is-active" only appears inside a sidebar <a> tag,
        # not in CSS (which uses ".mv-sidebar-link.is-active" with a dot).
        active_marker = "mv-sidebar-link is-active"
        self.assertIn(active_marker, content)
        active_idx = content.index(active_marker)
        # The href of the active entry follows within the same <a> tag.
        # Grab a window large enough to span the tag but not the next sibling.
        window = content[active_idx : active_idx + 200]
        self.assertIn(alpha_link, window)
        self.assertNotIn(beta_link, window)


class AppVersionContextProcessorTest(SimpleTestCase):
    """Verify that the app_version context processor injects APP_VERSION."""

    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_app_version_appears_in_index_response(self):
        # The base template renders "v{{ APP_VERSION }}" in the sidebar footer.
        # settings.APP_VERSION is "0.1.0", so the rendered text is "v0.1.0".
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0.1.0")

    def test_app_version_appears_in_document_response(self):
        _write_md(self.docs_path, "version-doc", "# Version test")
        _clear_caches()
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/version-doc/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0.1.0")


class RenderDocCachingTest(SimpleTestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_file_is_read_only_once_for_identical_path_and_mtime(self):
        path = _write_md(self.docs_path, "cached-doc", "# Cache Test")
        path_str = str(path)
        mtime = path.stat().st_mtime

        with patch.object(Path, "read_text", wraps=path.read_text) as mock_read:
            views._render_doc(path_str, mtime)
            views._render_doc(path_str, mtime)

        self.assertEqual(mock_read.call_count, 1)


class LoadMetaCachingTest(SimpleTestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_file_is_read_only_once_for_identical_path_and_mtime(self):
        path = _write_md(self.docs_path, "meta-doc", "# Meta Test")
        path_str = str(path)
        mtime = path.stat().st_mtime

        with patch.object(Path, "read_text", wraps=path.read_text) as mock_read:
            views._load_meta(path_str, mtime)
            views._load_meta(path_str, mtime)

        self.assertEqual(mock_read.call_count, 1)


class FrontmatterTest(SimpleTestCase):
    """Verify that YAML frontmatter is parsed and surfaced in views."""

    def setUp(self):
        self.client = Client()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.docs_path = Path(self.tmpdir.name)
        _write_md(
            self.docs_path,
            "with-meta",
            "---\ntitle: Full Title\ncategory: Guides\nsummary: A short summary.\nupdated: 2026-01-01\nread_time: 5\n---\n\n# Content",
        )
        _clear_caches()

    def tearDown(self):
        _clear_caches()
        self.tmpdir.cleanup()

    def test_frontmatter_title_appears_in_document_view(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/with-meta/")
        self.assertContains(response, "Full Title")

    def test_frontmatter_category_appears_in_document_view(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/with-meta/")
        self.assertContains(response, "Guides")

    def test_frontmatter_summary_appears_in_index_view(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/")
        self.assertContains(response, "A short summary.")

    def test_frontmatter_is_not_rendered_as_markdown_content(self):
        with patch.object(views.settings, "DOCS_DIR", self.docs_path):
            response = self.client.get("/docs/with-meta/")
        # The raw YAML block must not appear in the rendered HTML body.
        self.assertNotContains(response, "read_time: 5")

    def test_load_meta_returns_correct_fields(self):
        path = self.docs_path / "with-meta.md"
        mtime = path.stat().st_mtime
        meta = views._load_meta(str(path), mtime)
        self.assertEqual(meta["title"], "Full Title")
        self.assertEqual(meta["category"], "Guides")
        self.assertEqual(meta["summary"], "A short summary.")


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
