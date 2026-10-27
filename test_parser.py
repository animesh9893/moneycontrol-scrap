#!/usr/bin/env python3
"""Test script to validate the moneycontrol parser on real articles.

Usage:
    python test_parser.py https://www.moneycontrol.com/news/business/...
"""

import sys
import urllib.request
import json
from datetime import datetime

import moneycontrol

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def datetime_serializer(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def fetch(url: str) -> bytes:
    """Fetch URL content."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def test_url(url: str) -> None:
    """Test parsing a single URL."""
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    print(f"{'='*80}\n")

    # Check if it's a valid article URL
    is_article = moneycontrol.is_article_url(url)
    print(f"✓ Is article URL: {is_article}")
    if not is_article:
        print("  WARNING: URL does not match article pattern")

    # Fetch the page
    print(f"\n→ Fetching page...")
    try:
        html = fetch(url).decode("utf-8", errors="replace")
        print(f"✓ Fetched {len(html)} bytes")
    except Exception as e:
        print(f"✗ Failed to fetch: {e}")
        return

    # Parse the article
    print(f"\n→ Parsing article...")
    try:
        article = moneycontrol.parse(html)
    except Exception as e:
        print(f"✗ Parse error: {e}")
        import traceback
        traceback.print_exc()
        return

    if article is None:
        print("✗ Parser returned None (not an article page)")
        return

    if not article.get("sections"):
        print("✗ No sections found (skipped)")
        return

    print(f"✓ Parsed successfully")

    # Display results
    print(f"\n{'─'*80}")
    print("HEADLINE")
    print(f"{'─'*80}")
    print(article.get("headline", "N/A"))

    if article.get("summary"):
        print(f"\n{'─'*80}")
        print("SUMMARY")
        print(f"{'─'*80}")
        print(article.get("summary"))

    if article.get("authors"):
        print(f"\n{'─'*80}")
        print("AUTHORS")
        print(f"{'─'*80}")
        for author in article["authors"]:
            print(f"  • {author['name']}")
            if author.get("profile_url"):
                print(f"    {author['profile_url']}")

    if article.get("section"):
        print(f"\n{'─'*80}")
        print("SECTION")
        print(f"{'─'*80}")
        print(f"  {article['section']}")

    if article.get("published_at"):
        print(f"\n{'─'*80}")
        print("PUBLISHED AT")
        print(f"{'─'*80}")
        print(f"  {article['published_at']}")

    if article.get("tags"):
        print(f"\n{'─'*80}")
        print("TAGS")
        print(f"{'─'*80}")
        for tag in article["tags"]:
            print(f"  • {tag}")

    print(f"\n{'─'*80}")
    print("BODY SECTIONS")
    print(f"{'─'*80}")
    for i, section in enumerate(article["sections"], 1):
        heading = section.get("heading") or "[No heading]"
        paragraphs = section.get("paragraphs", [])
        tokens = sum(len(p) // 4 for p in paragraphs)
        print(f"\nSection {i}: {heading}")
        print(f"  Paragraphs: {len(paragraphs)}, ~{tokens} tokens")
        for j, para in enumerate(paragraphs[:2], 1):  # Show first 2 paragraphs
            preview = para[:120] + "..." if len(para) > 120 else para
            print(f"    {j}. {preview}")
        if len(paragraphs) > 2:
            print(f"    ... and {len(paragraphs) - 2} more paragraphs")

    if article.get("links"):
        print(f"\n{'─'*80}")
        print(f"LINKS ({len(article['links'])} found)")
        print(f"{'─'*80}")
        for i, (href, anchor) in enumerate(article["links"][:10], 1):
            anchor_text = anchor[:50] + "..." if len(anchor) > 50 else anchor
            print(f"  {i}. {anchor_text}")
            print(f"     → {href[:80]}")
        if len(article["links"]) > 10:
            print(f"  ... and {len(article['links']) - 10} more links")

    # Summary
    print(f"\n{'─'*80}")
    print("SUMMARY")
    print(f"{'─'*80}")
    print(f"  Headline: ✓")
    print(f"  Authors: {'✓' if article.get('authors') else '○'}")
    print(f"  Tags: {'✓' if article.get('tags') else '○'}")
    print(f"  Section: {'✓' if article.get('section') else '○'}")
    print(f"  Published At: {'✓' if article.get('published_at') else '○'}")
    print(f"  Summary: {'✓' if article.get('summary') else '○'}")
    print(f"  Image: {'✓' if article.get('image_url') else '○'}")
    print(f"  Body Sections: {len(article['sections'])} sections")
    print(f"  Links: {len(article.get('links', []))} links")
    print()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python test_parser.py <url> [<url2> ...]")
        print("\nExample:")
        print("  python test_parser.py https://www.moneycontrol.com/news/business/markets/...")
        sys.exit(1)

    for url in sys.argv[1:]:
        try:
            test_url(url)
        except KeyboardInterrupt:
            print("\nInterrupted")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
