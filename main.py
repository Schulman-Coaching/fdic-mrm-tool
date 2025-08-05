"""
Main CLI interface for FDIC MRM Data Collection Tool
"""
import asyncio
import click
import logging
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from config import settings
from database import db_manager
from data_parser import data_parser
from fdic_collector import collect_fdic_data
from export_handler import export_handler
from linkedin_collector import LinkedInCollector
from mrm_extractor import extract_mrm_data_for_banks

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOGS_DIR / "fdic_mrm_tool.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
console = Console()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """FDIC MRM Data Collection and Management Tool"""
    console.print(Panel.fit(
        "[bold blue]FDIC MRM Data Collection Tool[/bold blue]\n"
        "Automated collection and management of Model Risk Management data for FDIC banks",
        border_style="blue"
    ))

@cli.command()
def init():
    """Initialize the database and import existing data"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Initialize database
            task1 = progress.add_task("Initializing database...", total=None)
            db_manager.create_tables()
            progress.update(task1, description="✓ Database initialized")
            
            # Import existing data
            task2 = progress.add_task("Importing existing 22-bank dataset...", total=None)
            imported_count = data_parser.import_existing_data()
            progress.update(task2, description=f"✓ Imported {imported_count} banks from existing dataset")
        
        console.print(f"[green]✓ Initialization complete! Imported {imported_count} banks.[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Initialization failed: {e}[/red]")
        logger.error(f"Initialization failed: {e}")

@cli.command()
@click.option('--limit', default=100, help='Number of banks to collect (default: 100)')
def collect():
    """Collect top FDIC banks and populate database"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Collecting FDIC bank data...", total=None)
            
            # Run async collection
            added_count = asyncio.run(collect_fdic_data())
            
            progress.update(task, description=f"✓ Added {added_count} new banks to database")
        
        console.print(f"[green]✓ Collection complete! Added {added_count} new banks.[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Collection failed: {e}[/red]")
        logger.error(f"Collection failed: {e}")

@cli.command()
@click.option('--min-assets', default=25, help='Minimum assets in millions (default: 25)')
@click.option('--max-assets', default=50000, help='Maximum assets in millions (default: 50,000 = $50B)')
@click.option('--limit', default=100, help='Number of banks to collect (default: 100)')
def collect_range():
    """Collect FDIC banks within specific asset range"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Convert max assets from millions to billions for the function
            max_assets_billions = max_assets / 1000
            
            task = progress.add_task(f"Collecting banks with ${min_assets}M-${max_assets_billions:.0f}B assets...", total=None)
            
            # Run async collection
            async def collect_asset_range_data():
                from fdic_collector import FDICCollector
                async with FDICCollector() as collector:
                    return await collector.populate_asset_range_banks(min_assets, max_assets_billions, limit)
            
            added_count = asyncio.run(collect_asset_range_data())
            
            progress.update(task, description=f"✓ Added {added_count} banks in asset range")
        
        console.print(f"[green]✓ Asset range collection complete! Added {added_count} banks with ${min_assets}M-${max_assets_billions:.0f}B assets.[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Asset range collection failed: {e}[/red]")
        logger.error(f"Asset range collection failed: {e}")

@cli.command()
@click.option('--format', 'export_format', default='xlsx', type=click.Choice(['csv', 'xlsx']), help='Export format')
@click.option('--filename', help='Custom filename for export')
@click.option('--filter-incomplete', is_flag=True, help='Only export banks with incomplete data')
def export(export_format, filename, filter_incomplete):
    """Export bank data to CSV or Excel"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Preparing export data...", total=None)
            
            # Get banks to export
            if filter_incomplete:
                banks = db_manager.get_banks_needing_research()
                progress.update(task, description=f"Found {len(banks)} banks needing research")
            else:
                banks = db_manager.get_all_banks()
                progress.update(task, description=f"Found {len(banks)} total banks")
            
            # Export data
            if export_format == 'csv':
                filepath = export_handler.export_to_csv(banks, filename)
            else:
                filepath = export_handler.export_to_excel(banks, filename)
            
            progress.update(task, description=f"✓ Exported to {filepath}")
        
        console.print(f"[green]✓ Export complete! File saved to: {filepath}[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Export failed: {e}[/red]")
        logger.error(f"Export failed: {e}")

@cli.command()
def template():
    """Generate research template for manual data collection"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Generating research template...", total=None)
            filepath = export_handler.export_research_template()
            progress.update(task, description=f"✓ Template generated: {filepath}")
        
        console.print(f"[green]✓ Research template generated: {filepath}[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Template generation failed: {e}[/red]")
        logger.error(f"Template generation failed: {e}")

@cli.command()
@click.option('--name', help='Search by bank name')
@click.option('--rank-min', type=int, help='Minimum asset rank')
@click.option('--rank-max', type=int, help='Maximum asset rank')
@click.option('--state', help='Filter by state')
@click.option('--size', type=click.Choice(['mega', 'large', 'regional', 'community', 'small']), help='Filter by size category')
@click.option('--incomplete', is_flag=True, help='Show only banks with incomplete data')
@click.option('--limit', default=20, help='Maximum number of results to show')
def search(name, rank_min, rank_max, state, size, incomplete, limit):
    """Search and display bank information"""
    try:
        # Build search parameters
        min_completeness = None
        if incomplete:
            min_completeness = 0.0
            has_mrm_data = False
        else:
            has_mrm_data = None
        
        # Perform search
        banks = db_manager.search_banks(
            name_pattern=name,
            asset_rank_min=rank_min,
            asset_rank_max=rank_max,
            size_category=size,
            state=state,
            min_completeness=min_completeness,
            has_mrm_data=has_mrm_data
        )
        
        # Limit results
        banks = banks[:limit]
        
        if not banks:
            console.print("[yellow]No banks found matching the criteria.[/yellow]")
            return
        
        # Display results in table
        table = Table(title=f"Search Results ({len(banks)} banks)")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Bank Name", style="magenta")
        table.add_column("State", style="green")
        table.add_column("Size", style="blue")
        table.add_column("MRM Data", style="yellow")
        table.add_column("Completeness", style="red")
        
        for bank in banks:
            has_mrm = "✓" if bank.mrm_departments or bank.leadership else "✗"
            completeness = f"{bank.completeness_score:.1%}"
            
            table.add_row(
                str(bank.asset_rank or "N/A"),
                bank.bank_name,
                bank.headquarters_state or "N/A",
                bank.size_category.value if bank.size_category else "N/A",
                has_mrm,
                completeness
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗ Search failed: {e}[/red]")
        logger.error(f"Search failed: {e}")

@cli.command()
def stats():
    """Display database statistics"""
    try:
        stats = db_manager.get_database_stats()
        banks = db_manager.get_all_banks()
        
        # Create statistics table
        table = Table(title="Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Banks", str(stats['total_banks']))
        table.add_row("Banks with MRM Data", str(stats['banks_with_mrm_data']))
        table.add_row("MRM Coverage", f"{stats['mrm_coverage_percentage']:.1f}%")
        table.add_row("Average Completeness", f"{stats['average_completeness_score']:.1%}")
        table.add_row("Pending Research Tasks", str(stats['pending_research_tasks']))
        table.add_row("Recent Collections", str(stats['recent_collection_activities']))
        
        console.print(table)
        
        # Size distribution
        size_dist = {}
        quality_dist = {}
        
        for bank in banks:
            # Size distribution
            size = bank.size_category.value if bank.size_category else 'unknown'
            size_dist[size] = size_dist.get(size, 0) + 1
            
            # Quality distribution
            quality = bank.quality_status.value
            quality_dist[quality] = quality_dist.get(quality, 0) + 1
        
        # Size distribution table
        size_table = Table(title="Size Distribution")
        size_table.add_column("Category", style="cyan")
        size_table.add_column("Count", style="magenta")
        size_table.add_column("Percentage", style="green")
        
        total = sum(size_dist.values())
        for category, count in sorted(size_dist.items()):
            percentage = f"{count/total*100:.1f}%" if total > 0 else "0%"
            size_table.add_row(category.title(), str(count), percentage)
        
        console.print(size_table)
        
        # Quality distribution table
        quality_table = Table(title="Data Quality Distribution")
        quality_table.add_column("Status", style="cyan")
        quality_table.add_column("Count", style="magenta")
        quality_table.add_column("Percentage", style="green")
        
        for status, count in sorted(quality_dist.items()):
            percentage = f"{count/total*100:.1f}%" if total > 0 else "0%"
            quality_table.add_row(status.title(), str(count), percentage)
        
        console.print(quality_table)
        
    except Exception as e:
        console.print(f"[red]✗ Stats retrieval failed: {e}[/red]")
        logger.error(f"Stats retrieval failed: {e}")

@cli.command()
@click.argument('bank_name')
def detail(bank_name):
    """Show detailed information for a specific bank"""
    try:
        bank = db_manager.get_bank_by_name(bank_name)
        
        if not bank:
            console.print(f"[red]Bank '{bank_name}' not found.[/red]")
            return
        
        # Basic information panel
        basic_info = f"""
[bold]Bank Name:[/bold] {bank.bank_name}
[bold]Asset Rank:[/bold] {bank.asset_rank or 'N/A'}
[bold]Total Assets:[/bold] ${bank.total_assets:,.0f}M ({bank.size_category.value if bank.size_category else 'N/A'})
[bold]Headquarters:[/bold] {bank.headquarters_city}, {bank.headquarters_state}
[bold]FDIC CERT ID:[/bold] {bank.fdic_cert_id or 'N/A'}
[bold]RSSD ID:[/bold] {bank.rssd_id or 'N/A'}
        """.strip()
        
        console.print(Panel(basic_info, title="Basic Information", border_style="blue"))
        
        # MRM Departments
        if bank.mrm_departments:
            dept_info = ""
            for dept in bank.mrm_departments:
                dept_info += f"[bold]{dept.department_name}[/bold]\n"
                if dept.key_functions:
                    dept_info += f"  Functions: {', '.join(dept.key_functions)}\n"
                if dept.parent_organization:
                    dept_info += f"  Parent: {dept.parent_organization}\n"
                dept_info += "\n"
            
            console.print(Panel(dept_info.strip(), title="MRM Departments", border_style="green"))
        
        # Leadership
        if bank.leadership:
            leadership_table = Table(title="Leadership Information")
            leadership_table.add_column("Name", style="cyan")
            leadership_table.add_column("Title", style="magenta")
            leadership_table.add_column("Department", style="green")
            leadership_table.add_column("Confidence", style="yellow")
            
            for leader in bank.leadership:
                leadership_table.add_row(
                    leader.name or "Unknown",
                    leader.title or "Unknown",
                    leader.department or "N/A",
                    f"{leader.confidence_score:.1%}"
                )
            
            console.print(leadership_table)
        
        # Data Quality
        quality_info = f"""
[bold]Completeness Score:[/bold] {bank.completeness_score:.1%}
[bold]Confidence Score:[/bold] {bank.confidence_score:.1%}
[bold]Quality Status:[/bold] {bank.quality_status.value}
[bold]Primary Source:[/bold] {bank.primary_source.value}
[bold]Last Updated:[/bold] {bank.last_updated.strftime('%Y-%m-%d %H:%M:%S') if bank.last_updated else 'N/A'}
[bold]Last Verified:[/bold] {bank.last_verified.strftime('%Y-%m-%d %H:%M:%S') if bank.last_verified else 'N/A'}
        """.strip()
        
        console.print(Panel(quality_info, title="Data Quality", border_style="yellow"))
        
        # Notes
        if bank.notes:
            console.print(Panel(bank.notes, title="Notes", border_style="red"))
        
    except Exception as e:
        console.print(f"[red]✗ Detail retrieval failed: {e}[/red]")
        logger.error(f"Detail retrieval failed: {e}")

@cli.command()
def tasks():
    """Show pending research tasks"""
    try:
        tasks = db_manager.get_pending_research_tasks(50)
        
        if not tasks:
            console.print("[yellow]No pending research tasks.[/yellow]")
            return
        
        table = Table(title=f"Pending Research Tasks ({len(tasks)})")
        table.add_column("Bank", style="cyan")
        table.add_column("Task Type", style="magenta")
        table.add_column("Priority", style="red")
        table.add_column("Created", style="green")
        table.add_column("Description", style="blue")
        
        for task in tasks:
            bank = db_manager.get_bank(task.bank_id)
            bank_name = bank.bank_name if bank else f"Bank ID {task.bank_id}"
            
            table.add_row(
                bank_name,
                task.task_type,
                str(task.priority),
                task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A',
                task.description[:50] + "..." if len(task.description or "") > 50 else task.description or ""
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗ Tasks retrieval failed: {e}[/red]")
        logger.error(f"Tasks retrieval failed: {e}")

@cli.command()
@click.option('--batch-size', default=5, help='Number of banks to process simultaneously')
@click.option('--asset-min', type=float, help='Minimum asset size in millions')
@click.option('--asset-max', type=float, help='Maximum asset size in millions')
@click.option('--incomplete-only', is_flag=True, help='Only extract data for banks with low completeness scores')
def extract_mrm(batch_size, asset_min, asset_max, incomplete_only):
    """Extract comprehensive MRM data from multiple sources for all banks"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Preparing MRM data extraction...", total=None)
            
            # Get banks to process
            if asset_min or asset_max:
                # Filter by asset range
                banks = db_manager.search_banks(
                    asset_rank_min=None,
                    asset_rank_max=None,
                    min_completeness=0.0 if incomplete_only else None
                )
                # Additional filtering by asset size
                if asset_min or asset_max:
                    filtered_banks = []
                    for bank in banks:
                        if bank.total_assets:
                            if asset_min and bank.total_assets < asset_min:
                                continue
                            if asset_max and bank.total_assets > asset_max:
                                continue
                        filtered_banks.append(bank)
                    banks = filtered_banks
            elif incomplete_only:
                banks = db_manager.get_banks_needing_research(limit=1000)
            else:
                banks = db_manager.get_all_banks()
            
            if not banks:
                progress.update(task, description="✗ No banks found matching criteria")
                console.print("[yellow]No banks found matching the specified criteria.[/yellow]")
                return
            
            progress.update(task, description=f"Starting MRM extraction for {len(banks)} banks...")
            
            # Run comprehensive extraction
            stats = asyncio.run(extract_mrm_data_for_banks(banks))
            
            progress.update(task, description=f"✓ MRM extraction completed")
            
            # Display results
            results_table = Table(title="MRM Data Extraction Results")
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Count", style="magenta")
            
            results_table.add_row("Banks Processed", str(stats.get('banks_processed', 0)))
            results_table.add_row("Banks Updated in DB", str(stats.get('banks_updated', 0)))
            results_table.add_row("LinkedIn Profiles Found", str(stats.get('linkedin_profiles_found', 0)))
            results_table.add_row("Sources Used", ', '.join(stats.get('sources_used', set())))
            results_table.add_row("Errors Encountered", str(stats.get('errors_encountered', 0)))
            results_table.add_row("Update Errors", str(stats.get('update_errors', 0)))
            
            console.print(results_table)
        
        console.print(f"[green]✓ MRM extraction complete! Processed {stats.get('banks_processed', 0)} banks.[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ MRM extraction failed: {e}[/red]")
        logger.error(f"MRM extraction failed: {e}")

@cli.command()
@click.argument('bank_name')
@click.option('--username', help='LinkedIn username (or set LINKEDIN_USERNAME env var)')
@click.option('--password', help='LinkedIn password (or set LINKEDIN_PASSWORD env var)')
@click.option('--limit', default=10, help='Maximum number of profiles to collect')
def linkedin(bank_name, username, password, limit):
    """Collect MRM leadership data from LinkedIn for a specific bank"""
    try:
        if not username and not settings.LINKEDIN_USERNAME:
            console.print("[red]LinkedIn username required. Use --username option or set LINKEDIN_USERNAME environment variable.[/red]")
            return
        
        if not password and not settings.LINKEDIN_PASSWORD:
            console.print("[red]LinkedIn password required. Use --password option or set LINKEDIN_PASSWORD environment variable.[/red]")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task(f"Collecting LinkedIn data for {bank_name}...", total=None)
            
            # Initialize LinkedIn collector
            collector = LinkedInCollector(username, password)
            
            try:
                # Collect leadership information
                leadership_info = collector.collect_bank_leadership(bank_name)
                
                if not leadership_info:
                    progress.update(task, description=f"✗ No MRM professionals found for {bank_name}")
                    console.print(f"[yellow]No MRM professionals found on LinkedIn for {bank_name}[/yellow]")
                    return
                
                # Find the bank in database
                bank = db_manager.get_bank_by_name(bank_name)
                if not bank:
                    progress.update(task, description=f"✗ Bank {bank_name} not found in database")
                    console.print(f"[red]Bank '{bank_name}' not found in database. Please add it first.[/red]")
                    return
                
                # Add leadership information to existing bank data
                existing_leadership = bank.leadership or []
                existing_urls = {leader.linkedin_url for leader in existing_leadership if leader.linkedin_url}
                
                new_leaders = []
                for leader in leadership_info:
                    if leader.linkedin_url not in existing_urls:
                        new_leaders.append(leader)
                
                if new_leaders:
                    # Update bank with new leadership data
                    bank.leadership.extend(new_leaders)
                    bank.last_updated = datetime.utcnow()
                    
                    # Recalculate completeness score
                    bank.completeness_score = bank.completeness_score  # Triggers recalculation
                    
                    # Update in database
                    db_manager.update_bank(bank.id if hasattr(bank, 'id') else None, bank)
                    
                    progress.update(task, description=f"✓ Added {len(new_leaders)} new LinkedIn profiles for {bank_name}")
                    
                    # Display results
                    table = Table(title=f"New LinkedIn Profiles for {bank_name}")
                    table.add_column("Name", style="cyan")
                    table.add_column("Title", style="magenta")
                    table.add_column("LinkedIn URL", style="blue")
                    
                    for leader in new_leaders:
                        table.add_row(
                            leader.name or "Unknown",
                            leader.title or "Unknown",
                            leader.linkedin_url or "N/A"
                        )
                    
                    console.print(table)
                else:
                    progress.update(task, description=f"✓ No new profiles found (all already exist)")
                    console.print(f"[yellow]All found LinkedIn profiles for {bank_name} already exist in database[/yellow]")
                
            finally:
                collector.close()
        
    except Exception as e:
        console.print(f"[red]✗ LinkedIn collection failed: {e}[/red]")
        logger.error(f"LinkedIn collection failed: {e}")

if __name__ == '__main__':
    cli()