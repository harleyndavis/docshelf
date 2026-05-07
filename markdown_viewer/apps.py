from django.apps import AppConfig


class MarkdownViewerConfig(AppConfig):
    name = "markdown_viewer"

    def ready(self):
        from django.conf import settings
        settings.DOCS_DIR.mkdir(exist_ok=True)
