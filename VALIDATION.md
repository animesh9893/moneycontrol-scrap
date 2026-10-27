# Validation Guide for Moneycontrol Scraper

This document explains how to validate the moneycontrol scraper implementation and ensure it's working correctly.

## Quick Start Validation

### 1. Verify Python Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Test the Parser Directly

```bash
# Test on a known Moneycontrol article URL
python test_parser.py "https://www.moneycontrol.com/news/business/markets/sensex-tests-82000-reliance-scales-all-time-high-12345678.html"
```

The test script will output:
- ✓ Article URL validation
- ✓ Content fetching status
- Parsed headline
- Article sections with paragraph counts
- Links extracted from the article
- Metadata (authors, tags, section, dates)

Expected output indicators:
```
✓ Is article URL: True
✓ Fetched XXXX bytes
✓ Parsed successfully

HEADLINE
────────────────────────────────────────────────────────────
[Article title]

BODY SECTIONS
────────────────────────────────────────────────────────────
Section 1: [Section heading]
  Paragraphs: 5, ~2000 tokens
    1. [First paragraph preview...]
    2. [Second paragraph preview...]
```

### 3. Validate Against mint-scrape Structure

The implementation follows the exact same structure as mint-scrape:

| Component | Comparison |
|---|---|
| Parser module | ✓ `moneycontrol.py` mirrors `livemint.py` |
| Functions | ✓ Same functions: `is_article_url()`, `parse()`, `clean()`, `meta()` |
| Return structure | ✓ Same dict keys: `headline`, `summary`, `section`, `authors`, `tags`, `sections`, `links` |
| Crawler | ✓ `crawler.py` is identical except parser import |
| Database | ✓ `schema.sql` has same tables, moneycontrol source seed |
| Requirements | ✓ Same packages: beautifulsoup4, lxml, psycopg |

### 4. Parser Validation Checklist

Run the test script on 3-5 different Moneycontrol articles and verify:

```python
article = moneycontrol.parse(html)

# Required fields
assert article is not None, "Page should parse"
assert article["headline"], "Headline must be non-empty"
assert article["sections"], "Must have at least one section"

# Section structure
for section in article["sections"]:
    assert "heading" in section
    assert "paragraphs" in section
    assert isinstance(section["paragraphs"], list)
    assert all(isinstance(p, str) for p in section["paragraphs"])

# Optional fields
assert isinstance(article.get("authors"), list), "Authors must be a list"
assert isinstance(article.get("tags"), list), "Tags must be a list"
assert isinstance(article.get("links"), list), "Links must be a list"
```

### 5. Database Connection Validation

Before running the crawler with a real database:

```bash
# Create a test Postgres instance
initdb -D /tmp/pgtest -U test
pg_ctl -D /tmp/pgtest -o "-p 54329 -k '' -c listen_addresses=127.0.0.1" start

# Test with local database
DATABASE_URL="postgresql://test@127.0.0.1:54329/postgres" \
  python crawler.py --max-pages 5 --max-depth 1

# Should output:
# moneycontrol: 0 feed items
# Scraped 0, skipped 0, failed 0; 0 still pending
```

This validates:
- ✓ Database connection works
- ✓ Schema creation succeeds
- ✓ Parser is properly imported
- ✓ Crawler can handle the parser output

### 6. Article URL Pattern Validation

Test the URL regex pattern:

```python
import moneycontrol

# Valid patterns
assert moneycontrol.is_article_url(
    "https://www.moneycontrol.com/news/business/markets/sensex-12345678.html"
)
assert moneycontrol.is_article_url(
    "https://www.moneycontrol.com/news/business/companies/tcs-share-price-q3-results-88888888.html"
)

# Invalid patterns (should be False)
assert not moneycontrol.is_article_url(
    "https://www.moneycontrol.com/news/business/"  # No ID
)
assert not moneycontrol.is_article_url(
    "https://www.moneycontrol.com/news/business/markets/sensex-trends?id=123"  # Query string
)
```

### 7. HTML Parsing Robustness

The parser should handle:

```python
# Missing optional metadata
html_no_author = "<h1>Title</h1><div><p>Body text</p></div>"
article = moneycontrol.parse(html_no_author)
assert article["authors"] == []  # Empty but valid

# Multiple sections
html_multi = """
<h1>Title</h1>
<div>
    <h2>Section 1</h2>
    <p>Text 1</p>
    <h2>Section 2</h2>
    <p>Text 2</p>
</div>
"""
article = moneycontrol.parse(html_multi)
assert len(article["sections"]) >= 2

# Lists and tables in body
html_list = """
<h1>Title</h1>
<div>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</div>
"""
article = moneycontrol.parse(html_list)
assert "- Item 1" in article["sections"][0]["paragraphs"][0]
```

### 8. Comparison with mint-scrape

To validate complete parity:

```bash
# Clone mint-scrape
git clone https://github.com/animesh9893/mint-scrape.git

# Compare key functions
diff -u mint-scrape/livemint.py moneycontrol/moneycontrol.py

# The main differences should be:
# - Regex pattern for article URLs (moneycontrol-specific)
# - HTML selectors (Moneycontrol's page structure)
# - Meta tag names (article vs page structure differences)
```

## Common Issues and Debugging

### Issue: "Parser returned None"

**Cause:** Page doesn't have `<h1>` or main body container.

**Debug:**
```python
from bs4 import BeautifulSoup

html = fetch(url).decode("utf-8")
soup = BeautifulSoup(html, "lxml")

# Check for headline
headline = soup.find("h1")
print(f"Headline found: {headline is not None}")

# Check for body
body_selectors = [
    "div.article-content",
    "div.article-body",
    "div.article-text",
    "article"
]
for selector in body_selectors:
    body = soup.select_one(selector)
    print(f"Body ({selector}): {body is not None}")
```

### Issue: "Failed to fetch"

**Cause:** Network error, timeout, or blocked by website.

**Debug:**
```bash
# Test with curl
curl -I "https://www.moneycontrol.com/news/business/..." \
  -H "User-Agent: Mozilla/5.0..."

# Should return 200 OK
```

### Issue: "No sections found"

**Cause:** Body found but no valid paragraphs extracted.

**Debug:**
```python
# Add debug prints to parser
import moneycontrol

html = fetch(url).decode("utf-8")
soup = BeautifulSoup(html, "lxml")

body = soup.select_one("div.article-content")
if body:
    all_elements = body.find_all(["h2", "h3", "p", "ul", "ol", "table"])
    print(f"Found {len(all_elements)} body elements")
    for el in all_elements[:5]:
        print(f"  {el.name}: {el.get_text()[:50]}")
```

## Performance Validation

Test the crawler with a reasonable workload:

```bash
# Test with 10 pages, depth 1
time DATABASE_URL="postgresql://..." python crawler.py \
  --max-pages 10 \
  --max-depth 1 \
  --delay 0.5

# Expected:
# - Completes in < 20 seconds (10 pages * 1s each + overhead)
# - Memory usage < 200MB
# - No database connection errors
```

## Final Validation Checklist

Before deploying to production:

- [ ] Parser successfully parses 5+ different Moneycontrol articles
- [ ] All required fields populated (headline, sections)
- [ ] Optional fields handled gracefully when missing
- [ ] URL pattern correctly identifies article URLs
- [ ] Links extracted and normalized properly
- [ ] Database connection validated with local test
- [ ] Schema creation succeeds
- [ ] Crawler handles parsing errors gracefully
- [ ] No hardcoded URLs or credentials in code
- [ ] GitHub Actions workflow configured with `DATABASE_URL` secret
- [ ] README documentation complete and accurate

## Testing with Real Database

Once everything validates locally:

```bash
# Set up real database (e.g., Layerbase PostgreSQL)
export DATABASE_URL="postgresql://user:pass@host.cloud.postgres.layerbase.io/db?sslmode=require"

# Verify connection
python -c "import psycopg; psycopg.connect('$DATABASE_URL').close(); print('✓ Connected')"

# Create schema
python crawler.py --max-pages 1

# Should output:
# moneycontrol: 0 feed items
# Scraped 0, skipped 0, failed 0; 0 still pending
```

This completes the validation!
