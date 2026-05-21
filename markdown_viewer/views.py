import frontmatter
import markdown
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from pygments.formatters import HtmlFormatter
from django.conf import settings
from django.http import Http404
from django.shortcuts import render

PYGMENTS_CSS = HtmlFormatter(style="monokai").get_style_defs(".codehilite")


def _prettify_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


@lru_cache(maxsize=128)
def _load_meta(path_str: str, mtime: float) -> dict:
    path = Path(path_str)
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    meta = dict(post.metadata)
    if not meta.get("read_time"):
        meta["read_time"] = max(1, round(len(post.content.split()) / 275))
    if not meta.get("updated"):
        meta["updated"] = datetime.fromtimestamp(mtime).date()
    tags = meta.get("tags", [])
    meta["tags"] = [str(t) for t in (tags if isinstance(tags, list) else [tags])]
    return meta


@lru_cache(maxsize=128)
def _render_doc(path_str: str, mtime: float) -> str:
    path = Path(path_str)
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    md = markdown.Markdown(
        extensions=[
            "abbr",
            "attr_list",
            "def_list",
            "fenced_code",
            "footnotes",
            "tables",
            "codehilite",
            "toc",
            "sane_lists",
        ],
    )
    md.preprocessors.deregister("html_block")
    md.inlinePatterns.deregister("html")
    return md.convert(post.content)


def index(request):
    docs_dir: Path = settings.DOCS_DIR
    doc_paths = sorted(docs_dir.glob("*.md"), key=lambda f: f.stem.lower())
    doc_infos = []
    for path in doc_paths:
        path_str = str(path)
        mtime = path.stat().st_mtime
        meta = _load_meta(path_str, mtime)
        doc_infos.append(
            {
                "slug": path.stem,
                "title": meta.get("title", "") or _prettify_slug(path.stem),
                "category": meta.get("category", ""),
                "summary": meta.get("summary", ""),
                "updated": meta.get("updated"),
                "read_time": meta.get("read_time"),
                "tags": meta.get("tags", []),
            }
        )
    all_tags = sorted(set(tag for info in doc_infos for tag in info["tags"]))
    documents = [
        {"slug": info["slug"], "title": info["title"], "tags": info["tags"]}
        for info in doc_infos
    ]
    return render(
        request,
        "markdown_viewer/index.html",
        {
            "documents": documents,
            "doc_infos": doc_infos,
            "all_tags": all_tags,
        },
    )


def document(request, slug: str):
    docs_dir: Path = settings.DOCS_DIR
    path = (docs_dir / slug).with_suffix(".md")

    if not path.exists() or not path.is_relative_to(docs_dir):
        raise Http404

    path_str = str(path)
    mtime = path.stat().st_mtime
    content = _render_doc(path_str, mtime)
    doc_meta = _load_meta(path_str, mtime)
    doc_paths = sorted(docs_dir.glob("*.md"), key=lambda f: f.stem.lower())
    documents = []
    for p in doc_paths:
        meta = _load_meta(str(p), p.stat().st_mtime)
        documents.append(
            {
                "slug": p.stem,
                "title": meta.get("title", "") or _prettify_slug(p.stem),
                "tags": meta.get("tags", []),
            }
        )
    return render(
        request,
        "markdown_viewer/document.html",
        {
            "title": slug,
            "content": content,
            "doc_meta": doc_meta,
            "documents": documents,
            "current_doc": slug,
            "pygments_css": PYGMENTS_CSS,
        },
    )
