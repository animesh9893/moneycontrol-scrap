# File Structure and Descriptions

Complete breakdown of all files in the moneycontrol scraper project.

## Core Implementation Files

### `crawler.py` (239 lines)
**Purpose:** Source-agnostic news crawling engine
**Key Responsibilities:**
- Fetches web pages via HTTP with proper User-Agent
- Reads RSS feeds and queues article URLs
- Claims pending URLs (with FOR UPDATE SKIP LOCKED for concurrency)
- Parses articles using the appropriate parser module
- Saves articles, authors, tags, chunks to PostgreSQL
- Handles errors and retries (3 attempts max)
- Splits articles into RAG chunks (~400 tokens each)
- Extracts and normalizes links between articles
- Prints progress and generates GitHub Actions output

**Key Functions:**
- `fetch(url)` - HTTP request with timeout/User-Agent
- `normalize(href, base)` - URL normalization (no query/fragment)
- `approx_tokens(text)` - Token count estimation
- `chunk(sections)` - RAG chunking
- `upsert_url()` - Insert/update URL in queue
- `queue_feeds()` - Parse RSS feeds
- `claim()` - Get next URL to process
- `save_article()` - Store article and metadata
- `crawl()` - Main crawl loop
- `main()` - CLI entry point

**Dependencies:** psycopg, BeautifulSoup, moneycontrol parser

---

### `moneycontrol.py` (166 lines)
**Purpose:** Moneycontrol-specific article parser
**Key Responsibilities:**
- Validates article URLs against Moneycontrol pattern
- Extracts article headline from H1
- Finds article body container (tries multiple CSS selectors)
- Extracts metadata from meta tags (og:, article:, etc.)
- Parses article sections with headings and paragraphs
- Handles lists and tables in article body
- Extracts author information
- Extracts publish/modify timestamps
- Extracts tags and section/category
- Extracts all links from article body
- Cleans whitespace and removes widget IDs

**Key Functions:**
- `is_article_url(url)` - Validates URL pattern
- `clean(text)` - Whitespace normalization
- `meta(soup, name)` - Extract meta tag content
- `to_datetime(value)` - Parse ISO timestamps
- `is_heading(el)` - Detect section headings
- `block_text(el)` - Extract text from lists/tables
- `sections(body)` - Group body into sections
- `parse(html)` - Main parsing function

**Parser Output:**
```python
{
    "headline": str,
    "summary": str | None,
    "section": str | None,
    "image_url": str | None,
    "published_at": datetime | None,
    "modified_at": datetime | None,
    "authors": [{"name": str, "profile_url": str | None}],
    "tags": [str],
    "sections": [{"heading": str | None, "paragraphs": [str]}],
    "links": [(href, anchor_text)],
}
```

---

### `schema.sql` (96 lines)
**Purpose:** PostgreSQL database schema (idempotent)
**Defines Tables:**

1. **sources** - News sites
   - `id` (primary key)
   - `slug` (unique, 'moneycontrol')
   - `name` ('Moneycontrol')
   - `base_url` ('https://www.moneycontrol.com')
   - `feed_urls` (array of RSS URLs)

2. **urls** - Crawl frontier
   - `id` (primary key)
   - `source_id` (FK to sources)
   - `url` (unique, normalized)
   - `status` (pending/done/failed/skipped)
   - `depth` (0 from RSS, +1 per hop)
   - `attempts` (retry counter)
   - `last_error` (error message)
   - `discovered_at`, `fetched_at` (timestamps)
   - Index on pending URLs

3. **articles** - Parsed articles
   - `id` (primary key)
   - `url_id` (FK, unique)
   - `source_id` (FK)
   - `headline` (required)
   - `summary`, `section`, `image_url`
   - `published_at`, `modified_at`
   - `scraped_at` (when crawler ran)
   - `content_hash` (SHA256 for edit detection)
   - Index on (source_id, published_at DESC)

4. **authors** - Writers
   - `id` (primary key)
   - `source_id` (FK)
   - `name`
   - `profile_url`
   - Unique constraint: (source_id, name)

5. **article_authors** - Relationships
   - `article_id` (FK)
   - `author_id` (FK)
   - Primary key: (article_id, author_id)

6. **tags** - Keywords
   - `id` (primary key)
   - `name` (unique, lowercased)

7. **article_tags** - Relationships
   - `article_id` (FK)
   - `tag_id` (FK)
   - Primary key: (article_id, tag_id)

8. **article_chunks** - RAG units
   - `id` (primary key)
   - `article_id` (FK)
   - `chunk_index` (order within article)
   - `heading` (from section)
   - `body` (text content)
   - `token_count` (for RAG)
   - `embedded_at` (vector DB sync flag)
   - Unique: (article_id, chunk_index)
   - Index on unembedded chunks

9. **links** - Link graph
   - `from_url_id` (FK)
   - `to_url_id` (FK)
   - `anchor_text` (link text)
   - `first_seen_at` (timestamp)
   - Primary key: (from_url_id, to_url_id)

**Moneycontrol Seed Data:**
```sql
INSERT INTO sources (slug, name, base_url, feed_urls)
VALUES (
    'moneycontrol',
    'Moneycontrol',
    'https://www.moneycontrol.com',
    ARRAY[
        'https://www.moneycontrol.com/rss/markets',
        'https://www.moneycontrol.com/rss/companies',
        'https://www.moneycontrol.com/rss/news',
        'https://www.moneycontrol.com/rss/trending'
    ]
)
ON CONFLICT (slug) DO NOTHING;
```

---

## Documentation Files

### `README.md` (209 lines)
**Purpose:** User-facing project documentation
**Contents:**
- Project overview
- How it works (diagram)
- Crawl rules and behavior
- Database schema reference
- Installation instructions (local)
- Running locally with environment setup
- GitHub Actions setup
- Command-line flags
- File descriptions
- Moneycontrol article structure
- Feed URL configuration
- Common queries

**Audience:** End users, developers integrating the scraper

---

### `VALIDATION.md` (267 lines)
**Purpose:** Testing and validation procedures
**Contents:**
- Quick start validation
- Python environment setup
- Direct parser testing (test_parser.py)
- mint-scrape structure comparison
- Parser validation checklist
- Database connection testing
- URL pattern validation
- HTML parsing robustness
- Comparison with original project
- Debugging guide for common issues
- Performance validation
- Final checklist
- Real database testing

**Audience:** QA, developers validating implementation

---

### `IMPLEMENTATION.md` (360 lines)
**Purpose:** Deep technical documentation
**Contents:**
- Project structure diagram
- Component analysis (crawler, parser, schema, dependencies)
- Data flow visualization
- Key validation points
- Crawl algorithm pseudocode
- Parallel safety mechanisms
- Performance characteristics
- Error handling details
- Comprehensive comparison matrix
- Conclusion and verification

**Audience:** Architects, maintainers, advanced users

---

### `FILES.md` (This file)
**Purpose:** File inventory and descriptions
**Contents:** Overview of every file in the project

---

## Configuration and Example Files

### `requirements.txt` (4 lines)
**Purpose:** Python dependencies
**Contents:**
```
beautifulsoup4==4.15.0  # HTML parsing
lxml==6.1.3             # XML parser backend
psycopg[binary]==3.3.6  # PostgreSQL client
feedparser==6.0.10      # RSS/XML parsing (optional)
```

---

### `.env.example` (8 lines)
**Purpose:** Environment variable template
**Contents:**
```
DATABASE_URL=postgresql://...  # Required
DELAY=1.0                       # Optional
MAX_PAGES=50                    # Optional
MAX_DEPTH=2                     # Optional
```

**Usage:**
```bash
cp .env.example .env
# Edit .env with real database URL
source .env
python crawler.py
```

---

### `.gitignore` (55 lines)
**Purpose:** Git exclusion rules
**Excludes:**
- `.env` files (credentials)
- `__pycache__/`, `*.pyc` (Python cache)
- `.venv/`, `venv/` (virtual environments)
- `.vscode/`, `.idea/` (IDE files)
- `output/`, `*.log` (generated files)
- `.DS_Store` (macOS files)

---

## Utility and Test Files

### `test_parser.py` (198 lines)
**Purpose:** Interactive parser testing utility
**Features:**
- Fetch real Moneycontrol articles
- Validate article URL pattern
- Parse HTML and display results
- Show headline, sections, links, metadata
- Provide validation summary
- Debug problematic pages
- Color-coded output (✓, ✗, ○)

**Usage:**
```bash
python test_parser.py https://www.moneycontrol.com/news/business/.../article.html
```

**Output:**
- Article URL validation status
- Fetch success/failure
- Parsed content preview
- Extracted metadata
- Section breakdown
- Link statistics

---

## GitHub Actions Workflow

### `.github/workflows/scrape.yml` (51 lines)
**Purpose:** Automated crawling in GitHub Actions
**Triggers:** Manual dispatch only (no schedule)
**Inputs:**
- `max_pages` (10/25/50/100/200, default 50)
- `max_depth` (1/2/3, default 2)
- `runs_left` (0-20, default 5)

**Steps:**
1. Checkout repository
2. Setup Python 3.11
3. Install dependencies
4. Run crawler with DATABASE_URL secret
5. Chain next run if URLs pending

**Features:**
- Concurrency control (only one run at a time)
- Parameterized inputs
- Automatic chaining when URLs remain
- Requires DATABASE_URL secret

**Setup:**
```bash
# 1. Add to GitHub secrets
gh secret set DATABASE_URL < .env

# 2. Enable Actions on repository
# 3. Manual trigger: Actions → Scrape news → Run workflow
```

---

## Summary by Category

### Core Logic (5 files, 462 lines)
- `crawler.py` - Main engine
- `moneycontrol.py` - Parser
- `schema.sql` - Database
- `requirements.txt` - Dependencies
- `.env.example` - Config template

### Documentation (4 files, 836 lines)
- `README.md` - User guide
- `VALIDATION.md` - Testing procedures
- `IMPLEMENTATION.md` - Technical details
- `FILES.md` - This inventory

### Configuration (2 files)
- `.gitignore` - Git rules
- `.github/workflows/scrape.yml` - CI/CD

### Utilities (1 file)
- `test_parser.py` - Parser testing

---

## Metrics

| Metric | Value |
|--------|-------|
| Total files | 11 |
| Python code | 462 lines |
| Documentation | 836 lines |
| Configuration | 109 lines |
| Doc/Code ratio | 1.8:1 |
| Total size | ~50 KB |

---

## File Dependencies

```
crawler.py
  ├─→ moneycontrol.py (parser)
  ├─→ schema.sql (database)
  ├─→ requirements.txt (dependencies)
  └─→ DATABASE_URL (environment)

test_parser.py
  ├─→ moneycontrol.py (parser)
  └─→ requirements.txt (dependencies)

.github/workflows/scrape.yml
  ├─→ crawler.py (script to run)
  ├─→ requirements.txt (dependencies)
  ├─→ DATABASE_URL (GitHub secret)
  └─→ moneycontrol.py (via crawler)

README.md, VALIDATION.md, IMPLEMENTATION.md
  └─→ Reference all other files
```

---

## Versioning

All files follow the mint-scrape v1 pattern with Moneycontrol-specific adaptations:

| Component | Version | Source |
|-----------|---------|--------|
| Schema | v1 | mint-scrape exact |
| Crawler | v1 | mint-scrape exact |
| Parser | v1 | mint-scrape template |
| Dependencies | Latest stable | As of 2026-10 |

---

## Future Extensions

When adding a new source (e.g., Economic Times):

1. Create `economictimes.py` - Parser module
2. Add to `crawler.py` PARSERS dict
3. Add seed row to `schema.sql`
4. Document in `README.md`
5. Test with `test_parser.py economictimes` URLs

No schema or crawler changes needed!
