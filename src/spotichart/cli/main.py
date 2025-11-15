"""
Command-Line Interface

Provides a robust CLI for the Spotichart using Click.
"""

import os
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..core import SpotifyServiceFactory, KworbScraper
from ..utils.logger import setup_logging
from ..utils.exceptions import SpotichartError
from ..utils.configuration_provider import ConfigurationProvider

console = Console()

# Initialize configuration provider
config = ConfigurationProvider()


@click.group()
@click.version_option(version="2.0.0", prog_name="Spotichart")
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """
    Spotichart - Create playlists from Kworb charts.

    A professional tool to automatically generate Spotify playlists
    based on the latest music charts from Kworb.net.
    """
    ctx.ensure_object(dict)
    log_level = 'DEBUG' if debug else os.getenv('LOG_LEVEL', 'INFO')
    ctx.obj['logger'] = setup_logging(log_level=log_level)


@cli.command()
@click.option(
    '--region',
    '-r',
    type=click.Choice(config.get_available_regions(), case_sensitive=False),
    default='brazil',
    help='Chart region to scrape'
)
@click.option(
    '--limit',
    '-l',
    type=int,
    default=int(os.getenv('PLAYLIST_LIMIT', '1000')),
    help=f'Number of tracks to include (default: {os.getenv("PLAYLIST_LIMIT", "1000")})'
)
@click.option(
    '--name',
    '-n',
    type=str,
    help='Custom playlist name (default: auto-generated)'
)
@click.option(
    '--public',
    is_flag=True,
    help='Make playlist public (default: private)'
)
@click.option(
    '--update-mode',
    '-u',
    type=click.Choice(['replace', 'append', 'new'], case_sensitive=False),
    default='replace',
    help='Update mode: replace (default), append, or new (always create new)'
)
@click.pass_context
def create(ctx, region, limit, name, public, update_mode):
    """
    Create or update a Spotify playlist from Kworb charts.

    By default, if a playlist with the same name exists, it will be updated.
    Use --update-mode to control this behavior:
    - replace (default): Update existing playlist, replacing all tracks
    - append: Update existing playlist, adding new tracks
    - new: Always create a new playlist

    Examples:
        spotichart create --region brazil --limit 500
        spotichart create --region brazil --limit 500 --update-mode append
        spotichart create --region brazil --limit 500 --update-mode new --name "Brazil 2024"
    """
    logger = ctx.obj['logger']

    try:
        # Validate configuration
        if not config.validate():
            console.print("[red]Error: Missing Spotify API credentials![/red]")
            console.print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file")
            console.print("See .env.example for reference")
            sys.exit(1)

        # Generate playlist name if not provided
        if not name:
            name = f"Top {limit} - {region.capitalize()} (Kworb)"

        console.print(f"\n[bold cyan]Playlist:[/bold cyan] {name}")
        console.print(f"[cyan]Region:[/cyan] {region}")
        console.print(f"[cyan]Tracks:[/cyan] {limit}")
        console.print(f"[cyan]Visibility:[/cyan] {'Public' if public else 'Private'}")
        console.print(f"[cyan]Update mode:[/cyan] {update_mode}\n")

        # Scrape tracks
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Scraping {region} charts...", total=None)

            with KworbScraper() as scraper:
                tracks = scraper.scrape_region(region, limit)

            progress.update(task, description=f"[green]Found {len(tracks)} tracks")

        if not tracks:
            console.print("[yellow]No tracks found![/yellow]")
            sys.exit(0)

        # Create or update Spotify playlist
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Authenticating with Spotify...", total=None)

            # Use new SOLID architecture with dependency injection
            service = SpotifyServiceFactory.create()

            progress.update(task, description="Processing playlist...")

            # Choose method based on update_mode
            if update_mode == 'new':
                # Always create new playlist
                playlist_url, added_count, failed_tracks = service.create_playlist_with_tracks(
                    name=name,
                    track_ids=[t['track'] for t in tracks],
                    description=f'Top {limit} from Kworb {region.capitalize()} charts',
                    public=public
                )
                was_updated = False
            else:
                # Smart create or update
                playlist_url, added_count, failed_tracks, was_updated = service.create_or_update_playlist(
                    name=name,
                    track_ids=[t['track'] for t in tracks],
                    description=f'Top {limit} from Kworb {region.capitalize()} charts',
                    public=public,
                    update_mode=update_mode
                )

        # Display results
        action = "updated" if was_updated else "created"
        console.print(f"\n[bold green]Playlist {action} successfully![/bold green]")
        console.print(f"[green]URL:[/green] {playlist_url}")
        console.print(f"[green]Tracks {action}:[/green] {added_count}")

        if was_updated:
            mode_desc = "replaced" if update_mode == 'replace' else "appended"
            console.print(f"[blue]Mode:[/blue] {mode_desc}")

        if failed_tracks:
            console.print(f"[yellow]Tracks not found:[/yellow] {len(failed_tracks)}")

        logger.info(f"Playlist {action}: {playlist_url}")

    except SpotichartError as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        logger.error(f"Playlist creation failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {str(e)}")
        logger.exception("Unexpected error occurred")
        sys.exit(1)


@cli.command()
@click.option(
    '--region',
    '-r',
    type=click.Choice(config.get_available_regions(), case_sensitive=False),
    required=True,
    help='Chart region to preview'
)
@click.option(
    '--limit',
    '-l',
    type=int,
    default=10,
    help='Number of tracks to preview (default: 10)'
)
@click.pass_context
def preview(ctx, region, limit):
    """
    Preview top tracks from a region without creating a playlist.

    Example:
        spotichart preview --region global --limit 20
    """
    logger = ctx.obj['logger']

    try:
        console.print(f"\n[bold cyan]Previewing {region.capitalize()} Charts[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Fetching {region} charts...", total=None)

            with KworbScraper() as scraper:
                tracks = scraper.scrape_region(region, limit)

        if not tracks:
            console.print("[yellow]No tracks found![/yellow]")
            return

        # Display tracks in a table
        table = Table(title=f"Top {len(tracks)} Tracks - {region.capitalize()}")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Track ID", style="magenta")

        for idx, track in enumerate(tracks, 1):
            table.add_row(str(idx), track['track'])

        console.print(table)
        console.print(f"\n[green]Total tracks found:[/green] {len(tracks)}")

    except SpotichartError as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        logger.error(f"Preview failed: {str(e)}")
        sys.exit(1)


@cli.command()
def regions():
    """List all available chart regions."""
    console.print("\n[bold cyan]Available Regions:[/bold cyan]\n")

    table = Table()
    table.add_column("Region", style="cyan")
    table.add_column("URL", style="magenta")

    for region in config.get_available_regions():
        url = config.get_kworb_url(region)
        table.add_row(region.capitalize(), url)

    console.print(table)


@cli.command()
@click.option(
    '--limit',
    '-l',
    type=int,
    default=50,
    help='Number of playlists to show (default: 50)'
)
@click.pass_context
def list_playlists(ctx, limit):
    """List your Spotify playlists."""
    logger = ctx.obj['logger']

    try:
        if not config.validate():
            console.print("[red]Error: Missing Spotify API credentials![/red]")
            sys.exit(1)

        console.print("\n[bold cyan]Your Spotify Playlists:[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading playlists...", total=None)

            service = SpotifyServiceFactory.create()
            playlists = service.list_playlists(limit=limit)

        if not playlists:
            console.print("[yellow]No playlists found![/yellow]")
            return

        table = Table()
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Tracks", justify="right", style="yellow")
        table.add_column("Public", justify="center", style="magenta")

        for idx, playlist in enumerate(playlists, 1):
            public_status = "✓" if playlist.get('public') else "✗"
            tracks_count = playlist['tracks']['total']
            table.add_row(
                str(idx),
                playlist['name'],
                str(tracks_count),
                public_status
            )

        console.print(table)
        console.print(f"\n[green]Total playlists:[/green] {len(playlists)}")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        logger.error(f"Failed to list playlists: {str(e)}")
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Display current configuration."""
    console.print("\n[bold cyan]Configuration:[/bold cyan]\n")

    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    # Check credentials
    client_id_status = "✓" if os.getenv("SPOTIFY_CLIENT_ID", "") else "✗"
    client_secret_status = "✓" if os.getenv("SPOTIFY_CLIENT_SECRET", "") else "✗"

    table.add_row(
        "Spotify Client ID",
        f"{'***' + os.getenv("SPOTIFY_CLIENT_ID", "")[-4:] if os.getenv("SPOTIFY_CLIENT_ID", "") else 'Not set'}",
        client_id_status
    )
    table.add_row(
        "Spotify Client Secret",
        f"{'***' + os.getenv("SPOTIFY_CLIENT_SECRET", "")[-4:] if os.getenv("SPOTIFY_CLIENT_SECRET", "") else 'Not set'}",
        client_secret_status
    )
    table.add_row("Redirect URI", os.getenv("REDIRECT_URI", "http://localhost:8888/callback"), "✓")
    table.add_row("Default Limit", str(int(os.getenv("PLAYLIST_LIMIT", "1000"))), "✓")
    table.add_row("Log Level", os.getenv("LOG_LEVEL", "INFO"), "✓")
    table.add_row("Log File", str(Path(__file__).parent.parent.parent / "logs" / "spotichart.log"), "✓")

    console.print(table)

    if config.validate():
        console.print("\n[green]Configuration is valid![/green]")
    else:
        console.print("\n[red]Configuration is incomplete![/red]")
        console.print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")


if __name__ == '__main__':
    cli(obj={})
