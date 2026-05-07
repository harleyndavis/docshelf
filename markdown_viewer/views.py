import markdown
from functools import lru_cache
from pathlib import Path
from django.conf import settings
from django.http import Http404
from django.shortcuts import render


@lru_cache(maxsize=128)
def _render_doc(path_str: str, mtime: float) -> str:
    path = Path(path_str)
    raw = path.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=[
            "abbr", "attr_list", "def_list", "fenced_code",
            "footnotes", "tables", "codehilite", "toc", "sane_lists",
        ],
    )
    md.preprocessors.deregister("html_block")
    md.inlinePatterns.deregister("html")
    return md.convert(raw)


def index(request):
    docs_dir: Path = settings.DOCS_DIR
    documents = sorted(
        [f.stem for f in docs_dir.glob("*.md")],
        key=str.lower,
    )
    return render(request, "markdown_viewer/index.html", {"documents": documents})


def document(request, slug: str):
    docs_dir: Path = settings.DOCS_DIR
    path = (docs_dir / slug).with_suffix(".md")

    if not path.exists() or not path.is_relative_to(docs_dir):
        raise Http404

    content = _render_doc(str(path), path.stat().st_mtime)
    return render(request, "markdown_viewer/document.html", {"title": slug, "content": content})
