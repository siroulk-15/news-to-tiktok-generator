# News-to-TikTok Generator (NTG)

**MVP V0.1** — Automated news collection, normalization, deduplication, and story creation pipeline.

## 📋 Overview

NTG is a Python application that:
1. **Collects** news from RSS feeds (BBC, CNN, Reuters)
2. **Normalizes** articles into a standard format
3. **Deduplicates** articles to find the same story from different sources
4. **Creates stories** by grouping related articles
5. **Stores** everything in SQLite

## 🎯 MVP V0.1 Scope

✅ **Included:**
- RSS feed collection from multiple sources
- Article normalization with Pydantic models
- SQLite database with proper schema
- Deduplication by content hash and title similarity
- CLI commands for pipeline management
- Comprehensive test suite

❌ **Not included in MVP V0.1:**
- Video generation
- Text-to-speech
- Media asset search
- TikTok publishing
- Advanced scoring/filtering
- Web dashboard

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo_url>
cd news-to-tiktok-generator

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m app init
```

### Configuration

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings (defaults are fine for MVP)
```

### Run Collection Pipeline

```bash
# Collect news from all RSS sources, deduplicate, and create stories
python -m app collect
```

Expected output:
```
🚀 Starting news collection pipeline...
   Config: development | DB: sqlite:///data/news.db

📡 Step 1: Collecting news from sources...
✓ BBC News: fetched=15, stored=12, duplicates=3
✓ CNN: fetched=18, stored=14, duplicates=4
✓ Reuters: fetched=20, stored=18, duplicates=2

🔄 Step 2: Deduplicating articles...
✓ Deduplication Summary:
  Articles processed: 44
  Stories created: 35
  Stories updated: 0
  Duplicates found: 9

============================================================
📊 PIPELINE SUMMARY
============================================================
✓ Collection:
  - Total fetched:  53
  - Total stored:   44
  - Duplicates:     9

✓ Deduplication:
  - Stories created: 35
  - Stories updated: 0
  - Duplicates found: 9

✓ Database:
  - Total articles: 44
  - Total stories:  35
============================================================

✅ News collection pipeline completed successfully!
```

## 📊 CLI Commands

### Core Commands

```bash
# Initialize database (run once)
python -m app init

# Run complete pipeline: collect → deduplicate
python -m app collect

# Show collection status
python -m app status

# List all articles (with limit)
python -m app articles --limit 10

# List all stories (with limit)
python -m app stories --limit 10

# Manually run deduplication
python -m app deduplicate --hours 24
```

## 🗂️ Project Structure

```
news-to-tiktok-generator/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point for: python -m app
│   ├── config.py             # Settings from .env
│   ├── logger.py             # Logging configuration
│   ├── models.py             # Pydantic models (NewsArticle, Story)
│   ├── database.py           # SQLAlchemy models and session management
│   ├── cli.py                # Click CLI commands
│   │
│   ├── sources/              # News source implementations
│   │   ├── __init__.py
│   │   ├── base.py           # BaseNewsSource abstract class
│   │   └── rss.py            # RSSNewsSource implementation
│   │
│   └── services/             # Business logic services
│       ├── __init__.py
│       ├── news_collector.py # Collects articles from sources
│       └── deduplicator.py   # Deduplicates articles → stories
│
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_models.py        # Pydantic models tests
│   ├── test_rss_source.py    # RSS source tests
│   ├── test_news_collector.py # Collector tests
│   └── test_deduplicator.py  # Deduplicator tests
│
├── data/                     # Data directory (SQLite database)
│   └── news.db              # Database file (auto-created)
│
├── .env.example             # Example environment configuration
├── .gitignore              # Git ignore file
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── setup.py              # (Optional) Python package setup
```

## 🏗️ Architecture

### Models

**NewsArticle (Pydantic):**
- `id`: Unique identifier
- `source`: Source name (e.g., "BBC")
- `title`, `summary`, `url`: Article content
- `published_at`: Publication date (optional)
- `language`, `country`: Metadata
- `content_hash`: SHA256 hash for deduplication

**Story (Pydantic):**
- `id`: Unique story ID (based on title hash)
- `title`, `summary`: Story content
- `status`: NEW, FILTERED, VERIFIED, etc.
- `source_count`: Number of sources for this story
- `scores`: insolite_score, relevance_score, confidence_score, virality_score

**NewsSource (DB):**
- Links articles to stories
- Tracks source reliability

### Database Schema

**news_articles** — Raw articles from feeds
- Indexed on: URL (unique), content_hash, source_domain

**stories** — Deduplicated story groups
- Indexed on: status, created_at

**sources** — Article-to-story mappings
- Tracks which articles belong to which story

### Deduplication Strategy

1. **Fast path**: Content hash matching (identical articles)
2. **Fallback**: Title similarity (SequenceMatcher, 75% threshold)
3. **Validation**: Check publication dates are within 24 hours

### Data Flow

```
┌─────────────────────────────────────┐
│ RSS Feeds (BBC, CNN, Reuters)       │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ RSSNewsSource.fetch()               │
│ → Parse RSS entries                 │
│ → Extract metadata                  │
│ → Generate content hash             │
│ → Return List[NewsArticle]          │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ NewsCollector.collect()             │
│ → Check for duplicates by URL       │
│ → Store in SQLite                   │
│ → Track statistics                  │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Deduplicator.deduplicate()          │
│ → Find similar articles             │
│ → Group into stories                │
│ → Create NewsSourceDB links         │
│ → Set story status=NEW              │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ SQLite Database                     │
│ → news_articles (44 records)        │
│ → stories (35 records)              │
│ → sources (44 links)                │
└─────────────────────────────────────┘
```

## 🧪 Testing

### Run all tests
```bash
pytest

# With coverage
pytest --cov=app

# Verbose output
pytest -v

# Specific test file
pytest tests/test_rss_source.py

# Specific test
pytest tests/test_rss_source.py::TestRSSNewsSource::test_fetch_valid_feed
```

### Test Coverage
- **test_models.py** — Pydantic model validation
- **test_rss_source.py** — RSS feed parsing, error handling
- **test_news_collector.py** — Article collection, duplicate handling
- **test_deduplicator.py** — Article grouping, story creation

All tests use temporary SQLite databases and don't affect production data.

## 📝 Configuration

Edit `.env` to customize:

```env
# Environment
APP_ENV=development              # 'development' or 'production'
DEBUG=true                       # Enable debug logging

# Database
DATABASE_URL=sqlite:///data/news.db

# News collection settings
NEWS_SCAN_INTERVAL=3600         # Seconds between collections

# Scoring thresholds (for future versions)
MIN_CONFIDENCE=0.80
MIN_INSOLITE_SCORE=0.65

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
```

## 🔄 Workflow

### Daily Pipeline (Example)

```bash
# 08:00 — Collect and deduplicate
0 8 * * * /usr/bin/python3 /app/app --collect

# 08:30 — Show status
30 8 * * * /usr/bin/python3 /app/app --status

# 09:00 — List today's stories (for manual review)
0 9 * * * /usr/bin/python3 /app/app --stories --limit 20
```

## 🔐 Security Notes

- ✅ Secrets are in `.env` (never in code)
- ✅ `.env` is in `.gitignore`
- ✅ No SQL injection (using SQLAlchemy ORM)
- ✅ URLs validated by Pydantic
- ✅ Safe HTML stripping in RSS parser
- ⚠️ Always validate RSS feeds from trusted sources

## 📦 Dependencies

- **sqlalchemy** — ORM and database management
- **pydantic** — Data validation and parsing
- **feedparser** — RSS feed parsing
- **click** — CLI framework
- **pytest** — Testing framework
- **python-dotenv** — Environment variable loading

See `requirements.txt` for versions.

## 🚀 Next Steps (V0.2+)

1. **V0.2** — Scoring and filtering
   - Implement insolite_score calculation
   - Add confidence scoring
   - Filter low-quality stories

2. **V0.3** — Multi-source verification
   - Add GDELT and NewsAPI sources
   - Implement fact-checking
   - Add claim validation

3. **V0.4** — Script generation
   - LLM-based script writing
   - TTS integration
   - Subtitle generation

4. **V0.5** — Video rendering
   - FFmpeg integration
   - Media asset download
   - Video composition

5. **V0.6** — Dashboard
   - Web UI for validation
   - Manual approval workflow
   - Analytics

6. **V0.7** — TikTok integration
   - OAuth setup
   - Content Publishing API
   - Publishing automation

7. **V1.0** — Production release
   - Full automation
   - Monitoring and alerting
   - Multi-account support

## 🐛 Troubleshooting

### Database locked error
```
sqlite3.OperationalError: database is locked
```
**Solution:** Close any other connections to the database, or increase timeout:
```python
# In app/database.py, change engine creation:
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 30}
)
```

### RSS feed connection timeout
```
urllib.error.URLError: <urlopen error timed out>
```
**Solution:** Check network connection or disable problematic feed source in `cli.py`

### Tests failing with import errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution:** Run from project root directory, or install package in development mode:
```bash
pip install -e .
```

## 📄 License

[Add your license here]

## 👥 Contributors

- NTG Team

## 📧 Contact

[Add contact information if needed]

---

**Status**: MVP V0.1 ✅ Complete
**Last Updated**: 2026-08-14
**Python Version**: 3.12+
