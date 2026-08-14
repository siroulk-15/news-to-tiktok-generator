"""Command-line interface for NTG."""

import sys
import click
from datetime import datetime

from app.database import init_db, get_db, close_db, NewsArticleDB, StoryDB
from app.services import NewsCollector, Deduplicator
from app.sources import RSSNewsSource
from app.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)


def get_default_rss_sources():
    """Get list of default RSS news sources."""
    return [
        RSSNewsSource("BBC News", "http://feeds.bbc.co.uk/news/rss.xml", country="GB"),
        RSSNewsSource("CNN", "http://rss.cnn.com/rss/cnn_topstories.rss", country="US"),
        RSSNewsSource("Reuters", "https://www.reuters.com/rssFeed/worldNews", country="US"),
    ]


@click.group()
def cli():
    """News-to-TikTok Generator CLI."""
    pass


@cli.command()
def init():
    """Initialize the database."""
    logger.info("Initializing database...")
    init_db()
    logger.info("✓ Database initialized successfully")


@cli.command()
@click.option("--limit", default=None, type=int, help="Limit number of articles to show")
def articles(limit):
    """List collected articles."""
    init_db()
    db = get_db()
    
    try:
        query = db.query(NewsArticleDB).order_by(NewsArticleDB.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        articles = query.all()
        
        if not articles:
            click.echo("No articles found.")
            return
        
        click.echo(f"\n📰 Articles ({len(articles)}):\n")
        click.echo(f"{'ID':<25} {'Source':<15} {'Title':<50} {'Date':<10}")
        click.echo("-" * 110)
        
        for article in articles:
            date_str = article.published_at.strftime("%Y-%m-%d") if article.published_at else "N/A"
            title_short = article.title[:47] + "..." if len(article.title) > 50 else article.title
            click.echo(f"{article.id:<25} {article.source:<15} {title_short:<50} {date_str:<10}")
        
        click.echo()
    finally:
        close_db(db)


@cli.command()
@click.option("--limit", default=None, type=int, help="Limit number of stories to show")
def stories(limit):
    """List created stories."""
    init_db()
    db = get_db()
    
    try:
        query = db.query(StoryDB).order_by(StoryDB.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        stories = query.all()
        
        if not stories:
            click.echo("No stories found.")
            return
        
        click.echo(f"\n📖 Stories ({len(stories)}):\n")
        click.echo(f"{'ID':<15} {'Title':<50} {'Status':<12} {'Sources':<8} {'Created':<10}")
        click.echo("-" * 100)
        
        for story in stories:
            title_short = story.title[:47] + "..." if len(story.title) > 50 else story.title
            created_str = story.created_at.strftime("%Y-%m-%d")
            click.echo(
                f"{story.id:<15} {title_short:<50} {story.status:<12} "
                f"{story.source_count:<8} {created_str:<10}"
            )
        
        click.echo()
    finally:
        close_db(db)


@cli.command()
@click.option("--hours", default=24, type=int, help="Dedup articles from last N hours")
def deduplicate(hours):
    """Deduplicate articles and create stories."""
    init_db()
    db = get_db()
    
    try:
        deduplicator = Deduplicator(db)
        stats = deduplicator.deduplicate(hours=hours)
        
        click.echo(f"\n✓ Deduplication completed successfully")
        for key, value in stats.items():
            click.echo(f"  {key}: {value}")
        click.echo()
    finally:
        close_db(db)


@cli.command()
def collect():
    """
    Collect news from RSS sources.
    
    This is the main command for MVP V0.1.
    """
    init_db()
    db = get_db()
    
    try:
        logger.info("\n🚀 Starting news collection pipeline...")
        logger.info(f"   Config: {settings.app_env} | DB: {settings.database_url}")
        
        # Step 1: Collect from sources
        click.echo("\n📡 Step 1: Collecting news from sources...")
        collector = NewsCollector(db)
        sources = get_default_rss_sources()
        
        collection_stats = collector.collect(sources)
        
        if collection_stats["errors"]:
            logger.warning(f"⚠ {len(collection_stats['errors'])} source error(s) occurred")
            for error in collection_stats["errors"]:
                logger.warning(f"  - {error}")
        
        # Step 2: Deduplicate
        click.echo("\n🔄 Step 2: Deduplicating articles...")
        deduplicator = Deduplicator(db)
        dedup_stats = deduplicator.deduplicate(hours=24)
        
        # Step 3: Summary
        total_articles = db.query(NewsArticleDB).count()
        total_stories = db.query(StoryDB).count()
        
        click.echo("\n" + "=" * 60)
        click.echo("📊 PIPELINE SUMMARY")
        click.echo("=" * 60)
        click.echo(f"✓ Collection:")
        click.echo(f"  - Total fetched:  {collection_stats['total_fetched']}")
        click.echo(f"  - Total stored:   {collection_stats['total_stored']}")
        click.echo(f"  - Duplicates:     {collection_stats['total_duplicates']}")
        click.echo(f"\n✓ Deduplication:")
        click.echo(f"  - Stories created: {dedup_stats['stories_created']}")
        click.echo(f"  - Stories updated: {dedup_stats['stories_updated']}")
        click.echo(f"  - Duplicates found: {dedup_stats['duplicates_found']}")
        click.echo(f"\n✓ Database:")
        click.echo(f"  - Total articles: {total_articles}")
        click.echo(f"  - Total stories:  {total_stories}")
        click.echo("=" * 60)
        
        logger.info("\n✅ News collection pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        close_db(db)


@cli.command()
def status():
    """Show pipeline status and statistics."""
    init_db()
    db = get_db()
    
    try:
        total_articles = db.query(NewsArticleDB).count()
        total_stories = db.query(StoryDB).count()
        
        click.echo("\n📊 NTG Status")
        click.echo("=" * 40)
        click.echo(f"Database:   {settings.database_url}")
        click.echo(f"Environment: {settings.app_env}")
        click.echo(f"\nStatistics:")
        click.echo(f"  Articles: {total_articles}")
        click.echo(f"  Stories:  {total_stories}")
        click.echo("=" * 40)
        click.echo()
    finally:
        close_db(db)


if __name__ == "__main__":
    cli()
