# Moneycontrol Scraper

A news crawler that stores articles from Moneycontrol in PostgreSQL in a clean, normalized form ready for RAG (retrieval for AI models). It starts from news feeds, scrapes every article, then follows the article links found inside each story, so older history comes in over time. A URL is scraped once and never again.

This is adapted from the [mint-scrape](https://github.com/animesh9893/mint-scrape) project to work with Moneycontrol.com instead of Livemint.

## How it works

```
RSS feeds ──► urls (pending, depth 0)
                 │
                 ▼  claim one pending URL (FOR UPDATE SKIP LOCKED)
            fetch page ──► source parser ──► articles, authors, tags,
                 │                           article_chunks, links
                 ▼
     same-site links in the article body
       ├─ looks like an article ─► urls (pending, depth + 1)
       └─ anything else ─────────► urls (skipped, never fetched)
```

Each run of `crawler.py`:

1. Applies `schema.sql` (idempotent, so the first run creates the tables).
2. Reads Moneycontrol's RSS feeds and queues article URLs at depth 0.
3. Repeatedly claims the shallowest, oldest `pending` URL with `depth <= --max-depth`, scrapes it, saves it, and queues its body links at `depth + 1`, until `--max-pages` pages are processed or nothing is pending.
4. Prints a summary and, in GitHub Actions, writes `pending=<n>` to `$GITHUB_OUTPUT` so the workflow can chain another run.

### Crawl rules

- **Scraped once:** `urls.url` is unique, and only `status = 'pending'` URLs are fetched. Once a URL is `done`, `skipped` or `failed`, it is never fetched again.
- **URL normalization:** links resolve against the page they appear on, query strings and `#fragments` are dropped, and the host is lowercased.
- **Same site only:** only links on the same host as `sources.base_url` are recorded. Same-site pages that are not articles are stored as `skipped`.
- **Depth:** depth 0 comes from RSS, and each link hop adds 1. A URL keeps the smallest depth it was ever found at.
- **Failures:** a URL that errors goes back to `pending` and is retried on later runs. After 3 attempts it becomes `failed`.
- **Concurrency:** claims use `FOR UPDATE SKIP LOCKED`, so parallel crawlers never scrape the same URL.
- **Politeness:** one request at a time, `--delay` seconds apart (default 1s).

## Database

PostgreSQL. All tables are in `schema.sql`.

| Table | One row per | Key columns |
|---|---|---|
| `sources` | news site | `slug` (matches the parser name), `base_url`, `feed_urls` |
| `urls` | URL ever seen; this is the crawl queue | `url` (unique), `status`, `depth`, `attempts`, `last_error` |
| `articles` | scraped article | `url_id`, `headline`, `summary`, `section`, `image_url`, `published_at`, `modified_at`, `content_hash` |
| `authors`, `article_authors` | writer per source, and article↔author | `name` unique per source, `profile_url` |
| `tags`, `article_tags` | lowercased keyword, and article↔tag | `name` (unique) |
| `article_chunks` | RAG text chunk | `article_id`, `chunk_index`, `heading`, `body`, `token_count` |
| `links` | link from one URL to another | `from_url_id`, `to_url_id`, `anchor_text` |

### RAG chunks

The body is not dumped as one blob. The parser returns the body as sections (a sub-heading and its paragraphs). The crawler packs each section's paragraphs into chunks of at most about 400 tokens, without splitting a paragraph or crossing a heading. Each chunk stores its `heading`, so a retrieved chunk reads on its own.

## Running it

### Locally

```sh
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# .env (git-ignored) holds: DATABASE_URL=postgresql://...?sslmode=require
set -a; source .env; set +a
./.venv/bin/python crawler.py --max-pages 50 --max-depth 2
```

| Flag | Default | Meaning |
|---|---|---|
| `--max-pages` | 50 | Pages to process this run |
| `--max-depth` | 2 | Deepest link hop to fetch |
| `--delay` | 1.0 | Seconds between requests |

### GitHub Actions

`.github/workflows/scrape.yml` runs only when triggered manually (**Actions → Scrape news → Run workflow**).

Setup:

1. Add the repository secret `DATABASE_URL`: **Settings → Secrets and variables → Actions**.
2. Enable Actions on your repository.

## Files

| File | Purpose |
|---|---|
| `crawler.py` | Source-agnostic crawler: feeds, queue, fetching, saving, chunking |
| `moneycontrol.py` | Moneycontrol parser; based on the livemint template |
| `schema.sql` | Tables, indexes and source seed rows; applied on every run |
| `requirements.txt` | `beautifulsoup4`, `lxml`, `psycopg[binary]`, `feedparser` |

## Moneycontrol Article Structure

Moneycontrol articles are parsed from the following HTML structure:

- **Headline:** `h1.article-headline` or generic `h1`
- **Body:** `div.article-content`, `div.article-body`, `div.article-text`, or generic article containers
- **Authors:** `span.author-name` or meta tag `author`
- **Publish/Modified dates:** `article:published_time`, `article:modified_time` meta tags
- **Section:** `article:section` meta tag
- **Image:** `og:image` meta tag
- **Summary:** `og:description` or `description` meta tag
- **Tags:** `keywords` meta tag (comma-separated)

Article URLs must match the pattern: `/news/business/...-\d{8,}\.html`

## Validation

The parser validates that:

1. Pages have both a headline (`h1`) and article body
2. The article body contains valid sections (headings + paragraphs)
3. Links are extracted and normalized properly
4. Metadata is extracted with fallbacks for different meta tag formats

## Adding Feed URLs

To update the RSS feeds for Moneycontrol, run:

```sql
UPDATE sources 
SET feed_urls = ARRAY[
    'https://www.moneycontrol.com/rss/markets',
    'https://www.moneycontrol.com/rss/companies',
    'https://www.moneycontrol.com/rss/news',
    'https://www.moneycontrol.com/rss/trending'
]
WHERE slug = 'moneycontrol';
```

Note: RSS availability on Moneycontrol may vary. Check their website for current feed URLs.

## Common Queries

```sql
-- Progress
SELECT status, depth, count(*) FROM urls GROUP BY 1, 2 ORDER BY 1, 2;

-- Articles by section
SELECT section, count(*) FROM articles GROUP BY section ORDER BY count DESC;

-- Recent articles
SELECT headline, published_at FROM articles ORDER BY published_at DESC LIMIT 10;

-- Failed URLs
SELECT url, attempts, last_error FROM urls WHERE status = 'failed' LIMIT 10;
```

## Known Limitations

- Moneycontrol's RSS feeds may have limited availability
- JavaScript-rendered content is not supported (only static HTML)
- Some articles may use dynamic content loading which won't be captured
- Authentication-required articles cannot be scraped
