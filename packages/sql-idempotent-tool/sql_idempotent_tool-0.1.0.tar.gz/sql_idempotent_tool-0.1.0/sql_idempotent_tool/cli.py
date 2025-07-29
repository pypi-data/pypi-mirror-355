"""CLI interface for the SQL Idempotent Tool."""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
import json

from .sql_parser import SQLParser, IdempotentTransformer
from .config import SQLIdempotentConfig, load_config, save_config, create_default_config_file, ConfigurableTransformer

app = typer.Typer(
    name="sql-idempotent",
    help="A CLI tool to add idempotent statements to SQL files",
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def config_init(
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to create config file"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config file")
) -> None:
    """
    Initialize a new configuration file with default settings.
    """
    if config_path is None:
        config_path = Path.cwd() / "sql-idempotent.toml"
    
    if config_path.exists() and not force:
        console.print(f"[red]Config file already exists at {config_path}[/red]")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)
    
    create_default_config_file(config_path)
    console.print(f"[green]✓ Created configuration file at {config_path}[/green]")


@app.command()
def config_show(
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file")
) -> None:
    """
    Show current configuration settings.
    """
    config = load_config(config_path)
    
    console.print("[bold blue]Current Configuration[/bold blue]")
    
    # Show transformation settings
    table = Table(title="Transformation Settings")
    table.add_column("Statement Type", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Strategy", style="yellow")
    
    for stmt_type, transform_config in config.transformations.items():
        table.add_row(
            stmt_type,
            "✓" if transform_config.enabled else "✗",
            transform_config.strategy
        )
    
    console.print(table)
    
    # Show parser settings
    console.print(f"\n[bold]Parser Settings:[/bold]")
    console.print(f"Case Sensitive: {config.parser.case_sensitive}")
    console.print(f"Ignore Comments: {config.parser.ignore_comments}")
    console.print(f"Excluded Types: {', '.join(config.parser.excluded_statement_types) or 'None'}")
    
    # Show output settings
    console.print(f"\n[bold]Output Settings:[/bold]")
    console.print(f"Preserve Formatting: {config.output.preserve_formatting}")
    console.print(f"Add Comments: {config.output.add_comments}")
    console.print(f"Create Backups: {config.create_backups}")


@app.command()
def config_set(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'transformations.CREATE_VIEW.enabled')"),
    value: str = typer.Argument(..., help="Configuration value"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file")
) -> None:
    """
    Set a configuration value.
    """
    config = load_config(config_path)
    
    # Parse the key path
    keys = key.split('.')
    current = config.model_dump()
    
    # Navigate to the parent of the target key
    for k in keys[:-1]:
        if k not in current:
            console.print(f"[red]Invalid configuration key: {key}[/red]")
            raise typer.Exit(1)
        current = current[k]
    
    # Set the value
    final_key = keys[-1]
    if final_key not in current:
        console.print(f"[red]Invalid configuration key: {key}[/red]")
        raise typer.Exit(1)
    
    # Convert value to appropriate type
    try:
        if isinstance(current[final_key], bool):
            value = value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(current[final_key], int):
            value = int(value)
        elif isinstance(current[final_key], float):
            value = float(value)
        # Keep as string for other types
    except ValueError:
        console.print(f"[red]Invalid value type for {key}[/red]")
        raise typer.Exit(1)
    
    current[final_key] = value
    
    # Save the updated config
    updated_config = SQLIdempotentConfig(**config.model_dump())
    if config_path is None:
        config_path = Path.cwd() / "sql-idempotent.toml"
    
    save_config(updated_config, config_path)
    console.print(f"[green]✓ Updated {key} = {value}[/green]")


@app.command()
def validate(
    file_path: Path = typer.Argument(..., help="Path to the SQL file to validate"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    strict: bool = typer.Option(False, "--strict", help="Fail on any non-idempotent statements")
) -> None:
    """
    Validate that a SQL file contains only idempotent statements.
    """
    if not file_path.exists():
        console.print(f"[red]Error: File {file_path} does not exist[/red]")
        raise typer.Exit(1)
    
    config = load_config(config_path)
    
    try:
        sql_content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)
    
    parser = SQLParser()
    statements = parser.parse_sql(sql_content)
    non_idempotent = parser.find_non_idempotent_statements(statements)
    
    # Filter based on configuration
    enabled_non_idempotent = [
        stmt for stmt in non_idempotent 
        if stmt['type'] not in config.parser.excluded_statement_types
    ]
    
    if not enabled_non_idempotent:
        console.print(f"[green]✓ {file_path} is fully idempotent![/green]")
        return
    
    console.print(f"[yellow]⚠ {file_path} contains {len(enabled_non_idempotent)} non-idempotent statements[/yellow]")
    
    table = Table(title="Non-Idempotent Statements")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Line", style="green")
    table.add_column("Enabled for Transform", style="yellow")
    
    for stmt in enabled_non_idempotent:
        line_num = sql_content[:stmt['start_byte']].count('\n') + 1
        transform_config = config.transformations.get(stmt['type'])
        enabled = transform_config.enabled if transform_config else True
        table.add_row(
            stmt['type'], 
            stmt['name'], 
            str(line_num),
            "✓" if enabled else "✗"
        )
    
    console.print(table)
    
    if strict:
        raise typer.Exit(1)


@app.command()
def analyze(
    file_path: Path = typer.Argument(..., help="Path to the SQL file to analyze"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
) -> None:
    """
    Analyze a SQL file and identify non-idempotent statements.
    """
    if not file_path.exists():
        console.print(f"[red]Error: File {file_path} does not exist[/red]")
        raise typer.Exit(1)
    
    if not file_path.is_file():
        console.print(f"[red]Error: {file_path} is not a file[/red]")
        raise typer.Exit(1)
    
    try:
        sql_content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)
    
    parser = SQLParser()
    statements = parser.parse_sql(sql_content)
    non_idempotent = parser.find_non_idempotent_statements(statements)
    
    console.print(f"\n[bold blue]Analysis Results for {file_path}[/bold blue]")
    console.print(f"Total statements found: {len(statements)}")
    console.print(f"Non-idempotent statements: {len(non_idempotent)}")
    
    if non_idempotent:
        table = Table(title="Non-Idempotent Statements")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Line", style="green")
        
        for stmt in non_idempotent:
            # Calculate approximate line number
            line_num = sql_content[:stmt['start_byte']].count('\n') + 1
            table.add_row(stmt['type'], stmt['name'], str(line_num))
        
        console.print(table)
        
        if verbose:
            console.print("\n[bold]Statement Details:[/bold]")
            for i, stmt in enumerate(non_idempotent, 1):
                console.print(f"\n[bold cyan]{i}. {stmt['type']} - {stmt['name']}[/bold cyan]")
                syntax = Syntax(stmt['text'], "sql", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"Original Statement"))
    else:
        console.print("[green]✓ All statements are already idempotent![/green]")


@app.command()
def transform(
    file_path: Path = typer.Argument(..., help="Path to the SQL file to transform"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path (default: overwrite input)"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of original file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed without modifying files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    safe_mode: Optional[bool] = typer.Option(None, "--safe-mode/--no-safe-mode", help="Use conditional blocks instead of DROP+CREATE to preserve dependencies"),
    format_sql: Optional[bool] = typer.Option(None, "--format/--no-format", help="Format output SQL using SQLFluff")
) -> None:
    """
    Transform a SQL file to make all statements idempotent.
    """
    if not file_path.exists():
        console.print(f"[red]Error: File {file_path} does not exist[/red]")
        raise typer.Exit(1)
    
    if not file_path.is_file():
        console.print(f"[red]Error: {file_path} is not a file[/red]")
        raise typer.Exit(1)
    
    try:
        original_content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)
    
    # Analyze first
    parser = SQLParser()
    statements = parser.parse_sql(original_content)
    non_idempotent = parser.find_non_idempotent_statements(statements)
    
    if not non_idempotent:
        console.print("[green]✓ All statements are already idempotent! No changes needed.[/green]")
        return
    
    # Transform with database configuration
    config = load_config(config_path)
    
    # Override safe_mode if provided via CLI
    if safe_mode is not None:
        config.database.safe_mode = safe_mode
    
    # Override format_sql if provided via CLI
    if format_sql is not None:
        config.output.format_sql = format_sql
    
    transformer = IdempotentTransformer(
        db_engine=config.database.engine,
        db_version=config.database.version,
        use_modern_syntax=config.database.use_modern_syntax,
        config=config
    )
    transformed_content = transformer.transform_sql_file(original_content)
    
    # Format the transformed content if enabled
    if config.output.format_sql:
        transformed_content = transformer.format_sql(transformed_content)
    
    console.print(f"\n[bold blue]Transformation Results for {file_path}[/bold blue]")
    console.print(f"Statements transformed: {len(non_idempotent)}")
    
    if verbose or dry_run:
        table = Table(title="Transformations Applied")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Transformation", style="yellow")
        
        for stmt in non_idempotent:
            transformation_type = _get_transformation_description(stmt['type'], config)
            table.add_row(stmt['type'], stmt['name'], transformation_type)
        
        console.print(table)
    
    if dry_run:
        console.print("\n[yellow]Dry run mode - no files were modified[/yellow]")
        if verbose:
            console.print("\n[bold]Transformed Content Preview:[/bold]")
            syntax = Syntax(transformed_content, "sql", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Transformed SQL"))
        return
    
    # Determine output path
    output_path = output or file_path
    
    # Create backup if requested and we're overwriting the original
    if backup and output_path == file_path:
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        try:
            backup_path.write_text(original_content, encoding='utf-8')
            console.print(f"[green]✓ Backup created: {backup_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating backup: {e}[/red]")
            raise typer.Exit(1)
    
    # Write transformed content
    try:
        output_path.write_text(transformed_content, encoding='utf-8')
        console.print(f"[green]✓ Transformed SQL written to: {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing output file: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def batch(
    directory: Path = typer.Argument(..., help="Directory containing SQL files"),
    pattern: str = typer.Option("*.sql", "--pattern", "-p", help="File pattern to match"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory (default: overwrite input files)"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of original files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed without modifying files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    format_sql: Optional[bool] = typer.Option(None, "--format/--no-format", help="Format output SQL using SQLFluff")
) -> None:
    """
    Transform multiple SQL files in a directory to make all statements idempotent.
    """
    if not directory.exists():
        console.print(f"[red]Error: Directory {directory} does not exist[/red]")
        raise typer.Exit(1)
    
    if not directory.is_dir():
        console.print(f"[red]Error: {directory} is not a directory[/red]")
        raise typer.Exit(1)
    
    # Find SQL files
    sql_files = list(directory.glob(pattern))
    if not sql_files:
        console.print(f"[yellow]No files matching pattern '{pattern}' found in {directory}[/yellow]")
        return
    
    console.print(f"\n[bold blue]Batch Processing {len(sql_files)} files[/bold blue]")
    
    total_transformed = 0
    total_statements = 0
    
    for sql_file in sql_files:
        console.print(f"\n[cyan]Processing: {sql_file.name}[/cyan]")
        
        try:
            original_content = sql_file.read_text(encoding='utf-8')
        except Exception as e:
            console.print(f"[red]  Error reading file: {e}[/red]")
            continue
        
        # Analyze
        parser = SQLParser()
        statements = parser.parse_sql(original_content)
        non_idempotent = parser.find_non_idempotent_statements(statements)
        
        if not non_idempotent:
            console.print("  [green]✓ Already idempotent[/green]")
            continue
        
        # Transform with database configuration
        config = load_config(config_path)
        
        # Override format_sql if provided via CLI
        if format_sql is not None:
            config.output.format_sql = format_sql
        
        transformer = IdempotentTransformer(
            db_engine=config.database.engine,
            db_version=config.database.version,
            use_modern_syntax=config.database.use_modern_syntax,
            config=config
        )
        transformed_content = transformer.transform_sql_file(original_content)
        
        # Format the transformed content if enabled
        if config.output.format_sql:
            transformed_content = transformer.format_sql(transformed_content)
        
        console.print(f"  [yellow]Transforming {len(non_idempotent)} statements[/yellow]")
        total_transformed += len(non_idempotent)
        total_statements += len(statements)
        
        if dry_run:
            continue
        
        # Determine output path
        if output_dir:
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / sql_file.name
        else:
            output_path = sql_file
        
        # Create backup if requested and we're overwriting the original
        if backup and output_path == sql_file:
            backup_path = sql_file.with_suffix(sql_file.suffix + '.backup')
            try:
                backup_path.write_text(original_content, encoding='utf-8')
            except Exception as e:
                console.print(f"  [red]Error creating backup: {e}[/red]")
                continue
        
        # Write transformed content
        try:
            output_path.write_text(transformed_content, encoding='utf-8')
            console.print(f"  [green]✓ Transformed[/green]")
        except Exception as e:
            console.print(f"  [red]Error writing output: {e}[/red]")
    
    console.print(f"\n[bold green]Batch processing complete![/bold green]")
    console.print(f"Files processed: {len(sql_files)}")
    console.print(f"Statements transformed: {total_transformed}")
    
    if dry_run:
        console.print("[yellow]Dry run mode - no files were modified[/yellow]")


def _get_transformation_description(stmt_type: str, config) -> str:
    """Get a human-readable description of the transformation applied."""
    # Check if safe mode is enabled
    if config.database.safe_mode:
        return "Conditional Block"
    
    # Create a temporary transformer to check version support
    transformer = IdempotentTransformer(
        db_engine=config.database.engine,
        db_version=config.database.version,
        use_modern_syntax=config.database.use_modern_syntax
    )
    
    # Check which transformation would be used based on version
    if stmt_type == 'CREATE_VIEW':
        return 'CREATE OR REPLACE VIEW'
    elif stmt_type == 'CREATE_MATERIALIZED_VIEW':
        if transformer._supports_feature("materialized_view_or_replace", "15"):
            return 'CREATE OR REPLACE MATERIALIZED VIEW'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'CREATE_TRIGGER':
        if transformer._supports_feature("trigger_or_replace", "14"):
            return 'CREATE OR REPLACE TRIGGER'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'CREATE_PROCEDURE':
        if transformer._supports_feature("procedure_or_replace", "11"):
            return 'CREATE OR REPLACE PROCEDURE'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'CREATE_POLICY':
        if transformer._supports_feature("policy_if_not_exists", "15"):
            return 'CREATE POLICY IF NOT EXISTS'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'CREATE_SEQUENCE':
        if transformer._supports_feature("sequence_if_not_exists", "10"):
            return 'CREATE SEQUENCE IF NOT EXISTS'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'CREATE_DOMAIN':
        if transformer._supports_feature("domain_if_not_exists", "11"):
            return 'CREATE DOMAIN IF NOT EXISTS'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'CREATE_ROLE':
        if transformer._supports_feature("role_if_not_exists", "8.1"):
            return 'CREATE ROLE IF NOT EXISTS'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'CREATE_USER':
        if transformer._supports_feature("user_if_not_exists", "8.1"):
            return 'CREATE USER IF NOT EXISTS'
        else:
            return 'DROP IF EXISTS + CREATE'
    elif stmt_type == 'ADD_CONSTRAINT':
        if transformer._supports_feature("constraint_if_not_exists", "9.6"):
            return 'ADD CONSTRAINT IF NOT EXISTS'
        else:
            return 'DROP IF EXISTS + ADD'
    
    # Fallback descriptions for other types
    descriptions = {
        'CREATE_TYPE': 'DROP IF EXISTS + CREATE',
        'CREATE_INDEX': 'CREATE INDEX IF NOT EXISTS',
        'CREATE_FUNCTION': 'CREATE OR REPLACE FUNCTION',
        'CREATE_SCHEMA': 'CREATE SCHEMA IF NOT EXISTS',
        'CREATE_EXTENSION': 'CREATE EXTENSION IF NOT EXISTS',
        'GRANT': 'REVOKE ALL + GRANT',
    }
    return descriptions.get(stmt_type, 'Unknown transformation')


if __name__ == "__main__":
    app()