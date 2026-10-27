"""Moneycontrol article parser. Same structure as livemint.py."""

import re
from datetime import datetime

from bs4 import BeautifulSoup

# Moneycontrol article URLs follow patterns like:
# https://www.moneycontrol.com/news/business/markets/sensex-nifty-....-12345678.html
# https://www.moneycontrol.com/news/business/companies/reliance-...-12345678.html
ARTICLE_URL = re.compile(r"^https://www\.moneycontrol\.com/news/business/[^\s?#]+-\d{8,}\.html$")
WIDGET_ID = re.compile(r"\s*Id:\d+")
SENTENCE_END = (".", "!", "?", ":", ";", '"', "'")


def is_article_url(url: str) -> bool:
    return bool(ARTICLE_URL.match(url))


def clean(text: str) -> str:
    """Clean whitespace and remove widget IDs."""
    return " ".join(WIDGET_ID.sub("", text).split())


def meta(soup: BeautifulSoup, name: str) -> str:
    """Extract meta tag content by property or name."""
    tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
    return tag["content"].strip() if tag and tag.get("content") else ""


def to_datetime(value: str) -> datetime | None:
    """Convert ISO format string to datetime."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def is_heading(el) -> bool:
    """Check if element is a heading (h2/h3 or bold-only paragraph)."""
    if el.name in ("h2", "h3"):
        return True
    # Moneycontrol also uses bold paragraphs as sub-headings
    bold = clean("".join(s.get_text() for s in el.find_all(["strong", "b"])))
    text = clean(el.get_text())
    return bool(text) and bold == text and len(text) < 150


def block_text(el) -> str:
    """Text of a body block; lists become '- item' lines and tables 'a | b' rows."""
    if el.name in ("ul", "ol"):
        items = [clean(li.get_text()) for li in el.find_all("li", recursive=False)]
        marker = (lambda i: f"{i}.") if el.name == "ol" else (lambda i: "-")
        return "\n".join(f"{marker(i)} {item}" for i, item in enumerate((t for t in items if t), 1))
    if el.name == "table":
        rows = [" | ".join(clean(cell.get_text()) for cell in tr.find_all(["th", "td"])) for tr in el.find_all("tr")]
        return "\n".join(row for row in rows if row.strip(" |"))
    return clean(el.get_text())


def sections(body) -> list[dict]:
    """Group body blocks under their sub-headings."""
    result = [{"heading": None, "paragraphs": []}]
    previous_tag = None

    for el in body.find_all(["h2", "h3", "p", "ul", "ol", "table"]):
        # Skip elements that are inside widgets or not in main content
        if not el.get_text().strip():
            continue

        text = block_text(el)
        if not text:
            continue

        # Check if this is a heading
        if el.name in ("h2", "h3", "p") and is_heading(el):
            result.append({"heading": text, "paragraphs": []})
            previous_tag = None
            continue

        paragraphs = result[-1]["paragraphs"]

        # Handle inline elements that split sentences
        if (el.name == previous_tag == "p" and paragraphs and
                not paragraphs[-1].endswith(SENTENCE_END) and text and text[0].islower()):
            paragraphs[-1] = f"{paragraphs[-1]} {text}"
        else:
            paragraphs.append(text)
        previous_tag = el.name

    return [s for s in result if s["paragraphs"]]


def parse(html: str) -> dict | None:
    """Parse moneycontrol article HTML and return article metadata."""
    soup = BeautifulSoup(html, "lxml")

    # Find the main article headline - Moneycontrol uses artTitle
    headline = (soup.find("h1", class_="artTitle") or
                soup.find("h1", class_="article_title") or
                soup.find("h1", class_="article-headline") or
                soup.find("h1"))

    # Find article body - Moneycontrol uses content_wrapper
    body = (soup.select_one("div.content_wrapper") or
            soup.select_one("div.arti-flow") or
            soup.select_one("div.article-content") or
            soup.select_one("div.article-body") or
            soup.select_one("div.article-text") or
            soup.select_one("div.storyContent") or
            soup.select_one("article") or
            soup.select_one("div[role='article']"))

    # If no headline or body, this is not an article
    if not body or not headline:
        return None

    # Extract author info
    author_elem = soup.find("span", class_="author-name") or soup.find("a", attrs={"data-author": True})
    author = clean(author_elem.get_text()) if author_elem else (meta(soup, "author") or None)

    author_link = soup.select_one('a[href*="/author/"]') or soup.select_one('a[href*="/authors/"]')

    # Get publish and modify times
    published_at = to_datetime(
        meta(soup, "article:published_time") or
        meta(soup, "datePublished") or
        meta(soup, "publish_date")
    )
    modified_at = to_datetime(
        meta(soup, "article:modified_time") or
        meta(soup, "dateModified") or
        meta(soup, "last-modified")
    )

    # Extract section/category
    section = (meta(soup, "article:section") or
               meta(soup, "news_keywords") or None)

    # Get image URL
    image_url = (meta(soup, "og:image") or
                 meta(soup, "twitter:image:src") or None)

    # Get summary/description
    summary = (meta(soup, "og:description") or
               meta(soup, "description") or
               meta(soup, "twitter:description") or None)

    # Get keywords/tags
    keywords = meta(soup, "keywords") or meta(soup, "article:tag") or ""
    tags = [t.strip().lower() for t in keywords.split(",") if t.strip()]

    # Parse body sections
    parsed_sections = sections(body)
    if not parsed_sections:
        return None

    # Extract all links from the body
    links = [(a.get("href", ""), clean(a.get_text())) for a in body.find_all("a", href=True)]

    return {
        "headline": clean(headline.get_text()),
        "summary": summary,
        "section": section,
        "image_url": image_url,
        "published_at": published_at,
        "modified_at": modified_at,
        "authors": [{"name": author, "profile_url": author_link.get("href") if author_link else None}] if author else [],
        "tags": tags,
        "sections": parsed_sections,
        "links": links,
    }
