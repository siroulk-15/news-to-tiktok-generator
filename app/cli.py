"""Command-line interface for NTG."""

import sys
import click
from datetime import datetime

from app.database import init_db, get_db, close_db, NewsArticleDB, StoryDB
from app.services import (
    NewsCollector,
    Deduplicator,
    StoryScorer,
    StorySelector,
    ScriptGenerator,
    EditorialWorkflow,
    ApprovedContentExporter,
    VideoRenderer,
)
from app.sources import RSSNewsSource
from app.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)


def get_default_rss_sources():
    """Get default RSS sources, prioritizing French-language coverage."""
    return [
        RSSNewsSource("France 24", "https://www.france24.com/fr/rss", country="FR", language="fr"),
        RSSNewsSource("RFI", "https://www.rfi.fr/fr/rss", country="FR", language="fr"),
        RSSNewsSource("Franceinfo", "https://www.francetvinfo.fr/titres.rss", country="FR", language="fr"),
        RSSNewsSource("Le Monde", "https://www.lemonde.fr/rss/tag/actualites.xml", country="FR", language="fr"),
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
@click.option("--hours", default=None, type=click.IntRange(min=1), help="Score stories updated in the last N hours")
def score(hours):
    """Calculate and persist V0.2 story scores."""
    init_db()
    db = get_db()

    try:
        stats = StoryScorer(db).score_stories(hours=hours)
        click.echo(f"\n✓ Scoring completed: {stats['stories_scored']} story(ies) scored\n")
    finally:
        close_db(db)


@cli.command()
@click.option("--min-insolite", default=None, type=click.FloatRange(0.0, 1.0))
@click.option("--min-confidence", default=None, type=click.FloatRange(0.0, 1.0))
@click.option("--limit", default=10, type=click.IntRange(min=1), help="Number of selected stories to display")
def select(min_insolite, min_confidence, limit):
    """Select and rank stories ready for downstream processing."""
    init_db()
    db = get_db()

    try:
        stats = StorySelector(db).select(
            min_insolite_score=(
                settings.min_insolite_score if min_insolite is None else min_insolite
            ),
            min_confidence=(
                settings.min_confidence if min_confidence is None else min_confidence
            ),
        )
        click.echo(
            f"\n✓ Selection: {stats['stories_selected']} selected, "
            f"{stats['stories_filtered']} filtered\n"
        )
        for story in stats["selected_stories"][:limit]:
            click.echo(
                f"  {story.id} | {story.insolite_score:.2f} insolite | "
                f"{story.confidence_score:.2f} confiance | {story.title}"
            )
        click.echo()
    finally:
        close_db(db)


@cli.command(name="scripts")
@click.option("--limit", default=10, type=click.IntRange(min=1), help="Number of selected stories to process")
def scripts(limit):
    """Generate safe draft scripts for selected stories."""
    init_db()
    db = get_db()

    try:
        stats = ScriptGenerator(db).generate_for_selected(limit=limit)
        click.echo(
            f"\n✓ Scripts: {stats['drafts_created']} created, "
            f"{stats['drafts_updated']} updated\n"
        )
    finally:
        close_db(db)


@cli.command()
@click.option("--limit", default=10, type=click.IntRange(min=1))
def review(limit):
    """List selected stories waiting for editorial review."""
    init_db()
    db = get_db()

    try:
        queue = EditorialWorkflow(db).review_queue(limit=limit)
        click.echo(f"\n✓ Review queue: {len(queue)} story(ies)\n")
        for story in queue:
            click.echo(
                f"  {story.id} | {story.insolite_score or 0.0:.2f} insolite | "
                f"{story.title}"
            )
        click.echo()
    finally:
        close_db(db)


@cli.command()
@click.argument("story_id")
def approve(story_id):
    """Approve a selected story and its draft."""
    init_db()
    db = get_db()

    try:
        EditorialWorkflow(db).approve(story_id)
        click.echo(f"\n✓ Story approved: {story_id}\n")
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    finally:
        close_db(db)


@cli.command()
@click.argument("story_id")
def reject(story_id):
    """Reject a selected story and its draft."""
    init_db()
    db = get_db()

    try:
        EditorialWorkflow(db).reject(story_id)
        click.echo(f"\n✓ Story rejected: {story_id}\n")
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    finally:
        close_db(db)


@cli.command(name="export-approved")
@click.option("--output", default="exports", show_default=True, type=click.Path(file_okay=False, dir_okay=True))
def export_approved(output):
    """Export approved scripts for manual video production."""
    init_db()
    db = get_db()

    try:
        stats = ApprovedContentExporter(db).export(output)
        click.echo(
            f"\n✓ Exported {stats['stories_exported']} approved story(ies) to "
            f"{stats['output_dir']}\n"
        )
    finally:
        close_db(db)


@cli.command(name="render-approved")
@click.option("--output", default="videos", show_default=True, type=click.Path(file_okay=False, dir_okay=True))
@click.option("--limit", default=None, type=click.IntRange(min=1))
def render_approved(output, limit):
    """Render approved scripts as silent vertical MP4 videos."""
    init_db()
    db = get_db()

    try:
        stats = VideoRenderer(db).render_approved(output, limit=limit)
        click.echo(
            f"\n✓ Rendered {stats['videos_rendered']} video(s) to "
            f"{stats['output_dir']}\n"
        )
    finally:
        close_db(db)


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, type=click.IntRange(1, 65535), show_default=True)
def web(host, port):
    """Start the local editorial web interface."""
    import uvicorn

    uvicorn.run("app.web:app", host=host, port=port, log_level="info")


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
        
        # Step 3: Score stories for downstream selection
        click.echo("\n⭐ Step 3: Scoring stories...")
        scoring_stats = StoryScorer(db).score_stories(hours=24)

        click.echo("\n🎯 Step 4: Selecting stories...")
        selection_stats = StorySelector(db).select(
            min_insolite_score=settings.min_insolite_score,
            min_confidence=settings.min_confidence,
        )

        click.echo("\n📝 Step 5: Generating script drafts...")
        script_stats = ScriptGenerator(db).generate_for_selected()

        # Step 6: Summary
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
        click.echo(f"\n✓ Scoring:")
        click.echo(f"  - Stories scored: {scoring_stats['stories_scored']}")
        click.echo(f"\n✓ Selection:")
        click.echo(f"  - Stories selected: {selection_stats['stories_selected']}")
        click.echo(f"  - Stories filtered: {selection_stats['stories_filtered']}")
        click.echo(f"\n✓ Script drafts:")
        click.echo(f"  - Drafts created: {script_stats['drafts_created']}")
        click.echo(f"  - Drafts updated: {script_stats['drafts_updated']}")
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
