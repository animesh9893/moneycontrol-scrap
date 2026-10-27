# Quick Start Guide

Get the Moneycontrol scraper running in 5 minutes.

## 1️⃣ Setup (2 min)

```bash
# Navigate to project
cd /path/to/moneycontrol

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env and add your DATABASE_URL
```

## 2️⃣ Test Parser (1 min)

```bash
# Test on a real Moneycontrol article
python test_parser.py "https://www.moneycontrol.com/news/business/markets/article-title-12345678.html"

# Expected output:
# ✓ Is article URL: True
# ✓ Fetched XXXX bytes
# ✓ Parsed successfully
# [Article headline, sections, links shown]
```

## 3️⃣ Run Locally (1 min)

```bash
# Set environment variable
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Run crawler with test database
DATABASE_URL="postgresql://test@localhost:5432/test" \
  python crawler.py --max-pages 5 --max-depth 1

# Expected output:
# moneycontrol: 0 feed items
# Scraped 0, skipped 0, failed 0; 0 still pending
```

## 4️⃣ Deploy to GitHub (1 min)

```bash
# Add database secret
gh secret set DATABASE_URL < .env

# Commit code
git add .
git commit -m "Add moneycontrol scraper"
git push

# Trigger manual workflow
# Via browser: GitHub → Your repo → Actions → "Scrape news" → Run workflow
# Or via CLI:
gh workflow run scrape.yml -f max_pages=50 -f max_depth=2
```

## Files Overview

| File | Purpose |
|------|---------|
| `crawler.py` | Main crawler engine |
| `moneycontrol.py` | Article parser |
| `schema.sql` | Database schema |
| `README.md` | Full documentation |
| `test_parser.py` | Test individual articles |
| `.env.example` | Configuration template |

## Key Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Test parser on URL
python test_parser.py "https://www.moneycontrol.com/news/business/.../article.html"

# Run crawler locally
python crawler.py --max-pages 50 --max-depth 2 --delay 1.0

# Check database
psql $DATABASE_URL -c "SELECT count(*) FROM articles;"
```

## Environment Variables

```bash
# Required
export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"

# Optional (defaults in crawler.py)
export DELAY=1.0          # Seconds between requests
export MAX_PAGES=50       # Pages to scrape per run
export MAX_DEPTH=2        # Maximum link depth to follow
```

## GitHub Actions Workflow

1. Go to your repository
2. Click **Actions** tab
3. Select **"Scrape news"** workflow
4. Click **"Run workflow"**
5. Configure inputs:
   - **max_pages**: 10-200 (default 50)
   - **max_depth**: 1-3 (default 2)
   - **runs_left**: 0-20 (default 5)

## Troubleshooting

### "DATABASE_URL is not set"
```bash
# Solution: Set environment variable
export DATABASE_URL="postgresql://..."
```

### "Parser returned None"
- Test URL is not an article (check URL pattern)
- Article requires JavaScript rendering
- Website structure changed

**Solution:**
```bash
python test_parser.py "https://www.moneycontrol.com/news/business/.../12345678.html"
# If it fails, article structure may need parser update
```

### "Connection refused"
- PostgreSQL not running
- Wrong hostname/port
- Wrong credentials

**Solution:**
```bash
# Test connection
psql "postgresql://user:pass@host:port/db" -c "SELECT 1;"
```

## Next Steps

1. **For users:** See [README.md](README.md)
2. **For developers:** See [IMPLEMENTATION.md](IMPLEMENTATION.md)
3. **For testing:** See [VALIDATION.md](VALIDATION.md)
4. **For details:** See [FILES.md](FILES.md)

## Common Operations

### Check progress
```sql
SELECT status, depth, count(*) FROM urls GROUP BY 1, 2 ORDER BY 1, 2;
```

### View recent articles
```sql
SELECT headline, published_at FROM articles ORDER BY published_at DESC LIMIT 10;
```

### Check failures
```sql
SELECT url, last_error FROM urls WHERE status = 'failed' LIMIT 5;
```

### Add more feed URLs
```sql
UPDATE sources 
SET feed_urls = ARRAY[
    'https://www.moneycontrol.com/rss/markets',
    'https://www.moneycontrol.com/rss/companies',
    -- Add more URLs here
]
WHERE slug = 'moneycontrol';
```

## Support Resources

- **Documentation:** README.md
- **Testing Guide:** VALIDATION.md
- **Technical Details:** IMPLEMENTATION.md
- **File Reference:** FILES.md
- **This Overview:** SUMMARY.md

## Ready?

```bash
# 1. Setup
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your DATABASE_URL

# 3. Test
python test_parser.py "https://www.moneycontrol.com/news/business/markets/article-12345678.html"

# 4. Run
python crawler.py --max-pages 10 --max-depth 1

# 5. Deploy
git push && gh workflow run scrape.yml
```

**You're ready!** 🚀
