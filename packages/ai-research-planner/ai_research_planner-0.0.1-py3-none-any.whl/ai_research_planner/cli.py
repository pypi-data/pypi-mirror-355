#!/usr/bin/env python3
"""Enhanced CLI with variable storage and smart cleaning options."""

import asyncio
import sys
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ai_research_planner.main import ResearchPlanner
from ai_research_planner.utils.config import Config
from ai_research_planner.models import ResearchPlan

app = typer.Typer(
    name="research-planner",
    help="AI-powered research planning and execution system",
    add_completion=False,
)
console = Console()

# Global variable storage for CLI results
cli_results = {}


def validate_complexity(value: str) -> str:
    """Validate complexity level."""
    valid_complexities = ["simple", "standard", "deep", "comprehensive"]
    if value not in valid_complexities:
        raise typer.BadParameter(f"Invalid complexity: {value}. Must be one of: {', '.join(valid_complexities)}")
    return value


@app.command()
def research(
    goal: str = typer.Argument(..., help="Research goal or question"),
    complexity: str = typer.Option(
        "standard",
        "--complexity",
        "-c",
        help="Research complexity level (simple, standard, deep, comprehensive)",
        callback=lambda ctx, param, value: validate_complexity(value) if value else "standard"
    ),
    output_dir: Path = typer.Option(
        Path("research_output"),
        "--output",
        "-o",
        help="Output directory for results",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to configuration file",
    ),
    save_plan: bool = typer.Option(
        False,
        "--save-plan",
        help="Save the research plan",
    ),
    skip_cleaning: bool = typer.Option(
        None,
        "--skip-cleaning",
        help="Skip data cleaning (auto-detected by default)",
    ),
    store_var: Optional[str] = typer.Option(
        None,
        "--store-var",
        help="Store results in named variable (e.g., 'my_results')",
    ),
    return_json: bool = typer.Option(
        False,
        "--json",
        help="Return results as JSON string",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """Execute a complete research workflow with enhanced options."""
    
    console.print(Panel.fit(
        f"🔬 AI Research Planner\n"
        f"Goal: {goal}\n"
        f"Complexity: {complexity}\n"
        f"Output: {output_dir}\n"
        f"Skip Cleaning: {'Auto-detect' if skip_cleaning is None else skip_cleaning}\n"
        f"Store Variable: {store_var or 'None'}",
        title="Starting Research",
        border_style="green"
    ))
    
    async def run_research():
        try:
            # Initialize planner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Initializing research planner...", total=None)
                
                config_path = str(config_file) if config_file else None
                planner = ResearchPlanner(config_path)
                
                progress.update(task, description="Creating research plan...")
                plan = await planner.create_plan(goal, complexity)
                
                if save_plan:
                    plan_file = output_dir / "research_plan.json"
                    plan_file.parent.mkdir(parents=True, exist_ok=True)
                    plan.save(str(plan_file))
                    console.print(f"📋 Plan saved to {plan_file}")
                
                progress.update(task, description="Executing research plan...")
                
                # Choose method based on storage preference
                if store_var or return_json:
                    if return_json:
                        results_data = await planner.research_to_json(goal, complexity, skip_cleaning)
                        result_type = "JSON string"
                    else:
                        results_data = await planner.research_to_variable(goal, complexity, skip_cleaning)
                        result_type = "dictionary"
                    
                    # Store in global variable if requested
                    if store_var:
                        cli_results[store_var] = results_data
                        console.print(f"📊 Results stored in variable '{store_var}' as {result_type}")
                    
                    # Extract summary for display
                    if return_json:
                        summary = json.loads(results_data)['summary']
                    else:
                        summary = results_data['summary']
                else:
                    # Standard execution with file saving
                    results = await planner.execute_plan(plan, skip_cleaning)
                    results.save(str(output_dir))
                    summary = results.get_summary()
                
                progress.update(task, description="Research completed! ✓")
            
            # Display results summary
            table = Table(title="Research Results Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Goal", goal)
            table.add_row("Complexity", complexity)
            table.add_row("Raw Data Items", str(summary["total_raw_items"]))
            table.add_row("Cleaned Data Items", str(summary["total_cleaned_items"]))
            table.add_row("Execution Steps", str(summary["execution_steps"]))
            table.add_row("Success Rate", f"{summary['metadata'].get('successful_steps', 0)}/{summary['execution_steps']}")
            
            if store_var:
                table.add_row("Variable Name", store_var)
                table.add_row("Variable Type", result_type)
            else:
                table.add_row("Output Directory", str(output_dir))
            
            console.print(table)
            
            if verbose and not return_json:
                console.print("\n📊 Sample Results:")
                # Handle both result types
                if store_var and not return_json:
                    sample_data = results_data.get('cleaned_data', [])[:3]
                else:
                    # This would need to be loaded from files for standard execution
                    console.print("   Use --store-var option to see sample results")
                
                if 'sample_data' in locals():
                    for i, item in enumerate(sample_data, 1):
                        title = item.get('title', 'Untitled')
                        url = item.get('url', 'No URL')
                        content = item.get('content', '')
                        console.print(f"\n{i}. **{title}**")
                        console.print(f"   URL: {url}")
                        content_preview = content[:200] + "..." if len(content) > 200 else content
                        console.print(f"   Preview: {content_preview}")
            
            # Show how to access stored variable
            if store_var:
                console.print(f"\n💡 Access your results:")
                console.print(f"   Python: cli_results['{store_var}']")
                if not return_json:
                    console.print(f"   URLs: [item['url'] for item in cli_results['{store_var}']['raw_data']]")
                    console.print(f"   Titles: [item['title'] for item in cli_results['{store_var}']['cleaned_data']]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Research interrupted by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            if verbose:
                console.print_exception()
            sys.exit(1)
    
    asyncio.run(run_research())


@app.command()
def show_variables():
    """Show all stored research variables."""
    if not cli_results:
        console.print("[yellow]No variables stored yet. Use --store-var option in research command.[/yellow]")
        return
    
    table = Table(title="Stored Research Variables")
    table.add_column("Variable Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Raw Items", style="yellow")
    table.add_column("Cleaned Items", style="blue")
    table.add_column("Goal", style="white")
    
    for var_name, data in cli_results.items():
        if isinstance(data, str):
            # JSON string
            parsed_data = json.loads(data)
            var_type = "JSON String"
            raw_count = len(parsed_data.get('raw_data', []))
            cleaned_count = len(parsed_data.get('cleaned_data', []))
            goal = parsed_data.get('summary', {}).get('goal', 'Unknown')
        else:
            # Dictionary
            var_type = "Dictionary"
            raw_count = len(data.get('raw_data', []))
            cleaned_count = len(data.get('cleaned_data', []))
            goal = data.get('summary', {}).get('goal', 'Unknown')
        
        table.add_row(var_name, var_type, str(raw_count), str(cleaned_count), goal[:50] + "..." if len(goal) > 50 else goal)
    
    console.print(table)


@app.command()
def get_variable(
    var_name: str = typer.Argument(..., help="Variable name to retrieve"),
    field: Optional[str] = typer.Option(None, "--field", help="Specific field to extract (raw_data, cleaned_data, summary)")
):
    """Get data from a stored variable."""
    if var_name not in cli_results:
        console.print(f"[red]Variable '{var_name}' not found. Use 'show-variables' to see available variables.[/red]")
        return
    
    data = cli_results[var_name]
    
    if isinstance(data, str):
        # JSON string
        parsed_data = json.loads(data)
        if field:
            result = parsed_data.get(field, f"Field '{field}' not found")
        else:
            result = parsed_data
    else:
        # Dictionary
        if field:
            result = data.get(field, f"Field '{field}' not found")
        else:
            result = data
    
    # Pretty print the result
    if isinstance(result, (dict, list)):
        console.print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        console.print(result)


# Rest of the CLI commands remain the same...
@app.command()
def plan(
    goal: str = typer.Argument(..., help="Research goal or question"),
    complexity: str = typer.Option(
        "standard",
        "--complexity",
        "-c",
        help="Research complexity level (simple, standard, deep, comprehensive)",
        callback=lambda ctx, param, value: validate_complexity(value) if value else "standard"
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for the plan",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to configuration file",
    ),
):
    """Create a research plan without executing it."""
    
    async def create_plan():
        try:
            config_path = str(config_file) if config_file else None
            planner = ResearchPlanner(config_path)
            
            console.print(f"🧠 Creating {complexity} research plan for: {goal}")
            plan = await planner.create_plan(goal, complexity)
            
            # Display plan
            console.print(Panel(
                f"**Goal:** {plan.goal}\n"
                f"**Complexity:** {plan.complexity}\n"
                f"**Steps:** {len(plan.steps)}\n"
                f"**Estimated Time:** {plan.estimate_total_time():.1f} minutes",
                title="Research Plan Created",
                border_style="blue"
            ))
            
            # Show steps
            table = Table(title="Research Plan Steps")
            table.add_column("Step", style="cyan", width=4)
            table.add_column("Action", style="green")
            table.add_column("Tool", style="yellow")
            table.add_column("Description", style="white")
            
            for i, step in enumerate(plan.steps, 1):
                table.add_row(
                    str(i),
                    step.action,
                    step.tool,
                    step.description
                )
            
            console.print(table)
            
            # Save plan if requested
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                plan.save(str(output_file))
                console.print(f"📋 Plan saved to {output_file}")
            
        except Exception as e:
            console.print(f"[red]Error creating plan: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(create_plan())


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    init: bool = typer.Option(False, "--init", help="Initialize default configuration"),
    validate: bool = typer.Option(False, "--validate", help="Validate configuration"),
    set_provider: Optional[str] = typer.Option(None, "--set-provider", help="Set AI provider"),
    set_model: Optional[str] = typer.Option(None, "--set-model", help="Set AI model"),
):
    """Manage configuration."""
    
    try:
        config = Config()
        
        if init:
            config.save()
            console.print("✅ Default configuration initialized")
            return
        
        if show:
            console.print(Panel(
                f"**Provider:** {config.get('ai_model.provider')}\n"
                f"**Model:** {config.get('ai_model.model_name')}\n"
                f"**Config File:** {config.config_path}",
                title="Current Configuration",
                border_style="blue"
            ))
        
        if validate:
            validation = config.validate_config()
            
            table = Table(title="Configuration Validation")
            table.add_column("Check", style="cyan")
            table.add_column("Status", style="bold")
            
            for check, status in validation.items():
                status_text = "[green]✅ Pass[/green]" if status else "[red]❌ Fail[/red]"
                table.add_row(check.replace('_', ' ').title(), status_text)
            
            console.print(table)
        
        if set_provider:
            config.set('ai_model.provider', set_provider)
            config.save()
            console.print(f"✅ Provider set to: {set_provider}")
        
        if set_model:
            config.set('ai_model.model_name', set_model)
            config.save()
            console.print(f"✅ Model set to: {set_model}")
        
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
