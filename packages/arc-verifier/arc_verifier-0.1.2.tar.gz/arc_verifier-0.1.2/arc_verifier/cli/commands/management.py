"""Management commands for Arc-Verifier CLI.

This module contains system setup and audit management commands:
- init: Environment initialization and configuration
- audit-list: Verification audit record management
"""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...security import AuditLogger
from ..initialization import (
    detect_system_capabilities,
    generate_env_config, 
    write_env_file,
    download_sample_data,
    display_init_results
)


console = Console()


@click.command()
@click.option("--env", type=click.Choice(["production", "staging", "development"]), default="development", help="Environment type")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init(env, force):
    """Initialize Arc-Verifier environment and configuration."""
    
    console.print("[bold blue]🚀 Initializing Arc-Verifier Environment[/bold blue]\n")
    
    # Check if already initialized
    env_file = Path.cwd() / ".env"
    if env_file.exists() and not force:
        console.print("[yellow]⚠️  Arc-Verifier already initialized (.env file exists)[/yellow]")
        console.print("Use --force to overwrite existing configuration")
        return
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        # Step 1: Detect capabilities
        task = progress.add_task("[cyan]Detecting system capabilities...", total=None)
        capabilities = detect_system_capabilities()
        progress.remove_task(task)
        
        # Step 2: Generate configuration
        task = progress.add_task("[cyan]Generating configuration...", total=None)
        config = generate_env_config(env, capabilities)
        progress.remove_task(task)
        
        # Step 3: Write .env file
        task = progress.add_task("[cyan]Writing configuration file...", total=None)
        write_env_file(config, env_file)
        progress.remove_task(task)
        
        # Step 4: Download sample data (if requested)
        if env == "development":
            task = progress.add_task("[cyan]Downloading sample market data...", total=None)
            download_sample_data()
            progress.remove_task(task)
    
    # Display results
    display_init_results(env, capabilities, config, console)


@click.command()
@click.option(
    "--image",
    help="Filter audits by image name",
)
@click.option(
    "--latest",
    is_flag=True,
    help="Show only the latest audit for each image",
)
def audit_list(image: str, latest: bool):
    """List verification audit records.

    Shows verification history and audit trail for transparency and compliance.

    Examples:
        arc-verifier audit-list
        arc-verifier audit-list --image shade/agent:latest
        arc-verifier audit-list --latest
    """
    console.print("[bold blue]Verification Audit Records[/bold blue]\n")

    audit_logger = AuditLogger()
    
    try:
        # Get audit records
        records = audit_logger.list_audits(image_filter=image)
        
        if not records:
            console.print("[yellow]No audit records found[/yellow]")
            if image:
                console.print(f"No records found for image: {image}")
            return
        
        # Display records in table format
        from rich.table import Table
        
        table = Table(title=f"Audit Records{f' for {image}' if image else ''}")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Image", style="green")
        table.add_column("Fort Score", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Tier", style="blue")
        
        # Filter to latest if requested
        if latest:
            seen_images = set()
            filtered_records = []
            for record in records:
                if record["image"] not in seen_images:
                    filtered_records.append(record)
                    seen_images.add(record["image"])
            records = filtered_records
        
        for record in records:
            timestamp = record.get("timestamp", "Unknown")
            if isinstance(timestamp, str):
                # Format timestamp if it's a string
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            image_name = record.get("image", "Unknown")
            fort_score = record.get("fort_score", "N/A")
            status = record.get("status", "Unknown")
            tier = "N/A"  # Not available in the list_audits format
            
            # Color code status
            if status == "PASSED":
                status = f"[green]{status}[/green]"
            elif status == "FAILED":
                status = f"[red]{status}[/red]"
            else:
                status = f"[yellow]{status}[/yellow]"
            
            table.add_row(
                str(timestamp),
                image_name[:40] + "..." if len(image_name) > 40 else image_name,
                str(fort_score),
                status,
                tier
            )
        
        console.print(table)
        console.print(f"\nTotal records: {len(records)}")
        
    except Exception as e:
        console.print(f"[red]Failed to retrieve audit records: {e}[/red]")
        raise click.ClickException(str(e))


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to fix configuration issues automatically")
def validate_config(fix):
    """Validate Arc-Verifier configuration and environment.
    
    Checks configuration files, API keys, system dependencies, and 
    verifies the environment is ready for agent verification.
    
    Examples:
        arc-verifier validate-config
        arc-verifier validate-config --fix
    """
    console.print("[bold blue]Validating Arc-Verifier Configuration[/bold blue]\n")
    
    issues = []
    warnings = []
    
    # Check .env file exists
    env_file = Path.cwd() / ".env"
    if not env_file.exists():
        issues.append("No .env file found. Run 'arc-verifier init' to create one.")
    else:
        console.print("[green]✓ .env file found[/green]")
        
        # Load and validate .env contents
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            console.print("[green]✓ .env file loaded successfully[/green]")
        except Exception as e:
            issues.append(f".env file cannot be loaded: {e}")
    
    # Check API keys
    import os
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not anthropic_key or anthropic_key.startswith("#"):
        warnings.append("ANTHROPIC_API_KEY not configured (LLM analysis will be limited)")
    else:
        console.print("[green]✓ Anthropic API key configured[/green]")
        
    if not openai_key or openai_key.startswith("#"):
        warnings.append("OPENAI_API_KEY not configured (GPT-4.1 analysis not available)")
    else:
        console.print("[green]✓ OpenAI API key configured[/green]")
    
    # Check Docker availability
    try:
        import docker
        client = docker.from_env()
        client.ping()
        console.print("[green]✓ Docker is available and running[/green]")
    except Exception as e:
        issues.append(f"Docker not available: {e}")
    
    # Check system capabilities
    capabilities = detect_system_capabilities()
    
    if capabilities["cpu_cores"] < 4:
        warnings.append(f"Low CPU cores ({capabilities['cpu_cores']}). Recommended: 4+")
    else:
        console.print(f"[green]✓ CPU cores: {capabilities['cpu_cores']}[/green]")
        
    if capabilities["memory_gb"] < 8:
        warnings.append(f"Low memory ({capabilities['memory_gb']}GB). Recommended: 8GB+")
    else:
        console.print(f"[green]✓ Memory: {capabilities['memory_gb']}GB[/green]")
    
    # Check TEE status
    if not capabilities["tee"]["available"]:
        warnings.append("TEE not available - using simulation mode (development only)")
    else:
        console.print(f"[green]✓ TEE available: {capabilities['tee']['platform']}[/green]")
    
    # Check data directory
    data_dir = Path.cwd() / "market_data"
    if not data_dir.exists():
        warnings.append("No market_data directory found. Run 'arc-verifier download-data' for sample data.")
    else:
        console.print("[green]✓ Market data directory exists[/green]")
    
    # Display results
    if issues:
        console.print("\n[red]Configuration Issues Found:[/red]")
        for issue in issues:
            console.print(f"  ❌ {issue}")
            
        if fix:
            console.print("\n[yellow]Attempting to fix issues...[/yellow]")
            if "No .env file found" in str(issues):
                console.print("Run 'arc-verifier init' to create configuration")
        
        raise click.ClickException("Configuration validation failed")
    
    if warnings:
        console.print("\n[yellow]Configuration Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  ⚠️  {warning}")
    
    console.print("\n[bold green]✅ Configuration validation passed![/bold green]")
    console.print("[dim]Your Arc-Verifier environment is ready for agent verification.[/dim]")


@click.command()
@click.option("--format", type=click.Choice(["table", "json", "env"]), default="table", help="Output format")
def show_config(format):
    """Display current Arc-Verifier configuration.
    
    Shows environment variables, system capabilities, and current settings
    used by Arc-Verifier for verification operations.
    
    Examples:
        arc-verifier show-config
        arc-verifier show-config --format json
        arc-verifier show-config --format env
    """
    console.print("[bold blue]Arc-Verifier Configuration[/bold blue]\n")
    
    # Load configuration
    import os
    from dotenv import load_dotenv
    
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        console.print(f"[green]Configuration loaded from: {env_file}[/green]\n")
    else:
        console.print("[yellow]No .env file found - using defaults[/yellow]\n")
    
    # Get system capabilities
    capabilities = detect_system_capabilities()
    
    # Collect configuration data
    config_data = {
        "environment": {
            "ARC_VERIFIER_ENV": os.getenv("ARC_VERIFIER_ENV", "development"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "ENABLE_AUDIT": os.getenv("ENABLE_AUDIT", "false"),
            "STRICT_VALIDATION": os.getenv("STRICT_VALIDATION", "false")
        },
        "api_keys": {
            "ANTHROPIC_API_KEY": "configured" if os.getenv("ANTHROPIC_API_KEY") and not os.getenv("ANTHROPIC_API_KEY").startswith("#") else "not configured",
            "OPENAI_API_KEY": "configured" if os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY").startswith("#") else "not configured"
        },
        "resource_limits": {
            "MAX_CONCURRENT_VERIFICATIONS": os.getenv("MAX_CONCURRENT_VERIFICATIONS", "8"),
            "MAX_CONCURRENT_SCANS": os.getenv("MAX_CONCURRENT_SCANS", "12"),
            "MAX_CONCURRENT_LLM": os.getenv("MAX_CONCURRENT_LLM", "6")
        },
        "tee_configuration": {
            "TEE_ENABLED": os.getenv("TEE_ENABLED", "false"),
            "TEE_PLATFORM": os.getenv("TEE_PLATFORM", "none"),
            "TEE_SIMULATION_MODE": os.getenv("TEE_SIMULATION_MODE", "true")
        },
        "data_configuration": {
            "MARKET_DATA_PATH": os.getenv("MARKET_DATA_PATH", "./market_data"),
            "CACHE_ENABLED": os.getenv("CACHE_ENABLED", "true")
        },
        "system_capabilities": {
            "docker_available": capabilities["docker"],
            "cpu_cores": capabilities["cpu_cores"],
            "memory_gb": capabilities["memory_gb"],
            "tee_available": capabilities["tee"]["available"],
            "tee_platform": capabilities["tee"]["platform"]
        }
    }
    
    # Display based on format
    if format == "json":
        console.print_json(data=config_data)
    elif format == "env":
        # Show as environment variable format
        for section, settings in config_data.items():
            if section != "system_capabilities":  # Skip read-only capabilities
                console.print(f"# {section.replace('_', ' ').title()}")
                for key, value in settings.items():
                    if key.endswith("_KEY") and value == "configured":
                        console.print(f"{key}=***")  # Hide actual key values
                    else:
                        console.print(f"{key}={value}")
                console.print()
    else:
        # Table format (default)
        from rich.table import Table
        
        # Environment settings
        env_table = Table(title="Environment Settings")
        env_table.add_column("Setting", style="cyan")
        env_table.add_column("Value", style="green")
        
        for key, value in config_data["environment"].items():
            env_table.add_row(key, str(value))
        
        console.print(env_table)
        
        # API configuration
        api_table = Table(title="API Configuration")
        api_table.add_column("Provider", style="cyan")
        api_table.add_column("Status", style="green")
        
        for key, value in config_data["api_keys"].items():
            provider = key.replace("_API_KEY", "").title()
            status_color = "green" if value == "configured" else "yellow"
            api_table.add_row(provider, f"[{status_color}]{value}[/{status_color}]")
        
        console.print(api_table)
        
        # System capabilities
        sys_table = Table(title="System Capabilities")
        sys_table.add_column("Capability", style="cyan")
        sys_table.add_column("Status", style="green")
        
        caps = config_data["system_capabilities"]
        sys_table.add_row("Docker", "✓ Available" if caps["docker_available"] else "❌ Not Available")
        sys_table.add_row("CPU Cores", str(caps["cpu_cores"]))
        sys_table.add_row("Memory", f"{caps['memory_gb']}GB")
        sys_table.add_row("TEE", f"✓ {caps['tee_platform']}" if caps["tee_available"] else "⚠️ Simulation Mode")
        
        console.print(sys_table)