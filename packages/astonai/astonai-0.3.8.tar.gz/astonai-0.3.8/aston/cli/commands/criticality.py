"""
Criticality CLI commands for TestIndex.

This module provides CLI commands for analyzing code criticality and 
tuning criticality weights.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aston.core.logging import get_logger
from aston.core.path_resolution import PathResolver
from aston.analysis.criticality_scorer import CriticalityScorer, CriticalityError

logger = get_logger(__name__)


@click.group()
def criticality():
    """Analyze code criticality and manage criticality weights."""
    pass


@criticality.command()
@click.option("--top", "-n", default=10, help="Number of top critical nodes to show")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option(
    "--nodes-file",
    type=click.Path(exists=True),
    help="Path to nodes.json file (default: .testindex/knowledge_graph/nodes.json)",
)
@click.option(
    "--edges-file",
    type=click.Path(exists=True),
    help="Path to edges.json file (default: .testindex/knowledge_graph/edges.json)",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to criticality weights config file",
)
@click.option("--verbose", is_flag=True, help="Show detailed scoring information")
@click.option(
    "--scorer",
    type=click.Choice(["auto", "go", "python"]),
    default="auto",
    help="Scorer implementation to use (auto: use Go if available, otherwise Python)",
)
@click.option(
    "--algorithm",
    type=str,
    default="degree",
    help="Algorithm to use (degree, pagerank, composite, betweenness)",
)
def analyze(
    top: int,
    output_format: str,
    nodes_file: Optional[str],
    edges_file: Optional[str],
    config: Optional[str],
    verbose: bool,
    scorer: str,
    algorithm: str,
):
    """Analyze repository criticality and show top critical nodes."""
    console = Console()

    try:
        # Check if Go scorer is explicitly requested but not available
        if scorer == "go":
            try:
                from aston.analysis.criticality_go import get_available_scorers

                go_available, _ = get_available_scorers()
                if not go_available:
                    console.print(
                        "[yellow]Warning:[/yellow] Go scorer requested but not available. Install aston-rank binary or use --scorer python."
                    )
                    console.print(
                        "See https://github.com/astonai/aston-rank for installation instructions."
                    )
                    raise click.Abort()
            except ImportError:
                console.print(
                    "[red]Error:[/red] Failed to check Go scorer availability."
                )
                raise click.Abort()

        # Initialize scorer based on the --scorer option
        if scorer in ("auto", "go"):
            try:
                from aston.analysis.criticality_go import create_scorer

                scorer_instance = create_scorer(scorer)
                is_go = True
            except (ImportError, Exception) as e:
                if scorer == "go":
                    console.print(f"[red]Error initializing Go scorer:[/red] {e}")
                    raise click.Abort()
                console.print(
                    "[yellow]Warning:[/yellow] Failed to initialize Go scorer, falling back to Python."
                )
                scorer_instance = CriticalityScorer()
                is_go = False
        else:
            # Python scorer explicitly requested
            scorer_instance = CriticalityScorer()
            is_go = False

        # Apply config for Python scorer only (Go scorer has its own config mechanism)
        if config and not is_go:
            scorer_instance = CriticalityScorer.from_config_file(Path(config))

        # Use default paths if not provided
        if nodes_file is None:
            nodes_file = str(PathResolver.nodes_file())
        if edges_file is None:
            edges_file = str(PathResolver.edges_file())

        nodes_path = Path(nodes_file)
        edges_path = Path(edges_file)

        if not nodes_path.exists():
            console.print(f"[red]Error:[/red] Nodes file not found: {nodes_path}")
            console.print(
                "[yellow]Tip:[/yellow] Run 'aston graph build' to generate knowledge graph files"
            )
            raise click.Abort()

        if not edges_path.exists():
            console.print(f"[red]Error:[/red] Edges file not found: {edges_path}")
            console.print(
                "[yellow]Tip:[/yellow] Run 'aston graph build' to generate knowledge graph files"
            )
            raise click.Abort()

        # Calculate criticality scores
        with console.status("[cyan]Calculating criticality scores..."):
            start_time = time.time()

            # Handle different scorer types
            if is_go:
                # Go scorer works directly with file paths
                top_critical_nodes = scorer_instance.get_top_critical_nodes(
                    nodes_file=nodes_path,
                    edges_file=edges_path,
                    limit=top,
                    algorithm=algorithm,
                    verbose=verbose,
                )
            else:
                # Load data for Python scorer
                with open(nodes_path, "r") as f:
                    nodes_data = json.load(f)

                with open(edges_path, "r") as f:
                    edges_data = json.load(f)

                # Handle both direct list and object with fields formats
                if isinstance(nodes_data, dict) and "nodes" in nodes_data:
                    nodes = nodes_data["nodes"]
                else:
                    nodes = nodes_data

                if isinstance(edges_data, dict) and "edges" in edges_data:
                    edges = edges_data["edges"]
                else:
                    edges = edges_data

                if verbose:
                    scorer_instance.weights.verbose_logging = True
                    scorer_instance.weights.export_intermediate_data = True

                top_critical_nodes = scorer_instance.get_top_critical_nodes(
                    nodes, edges, top_k=top
                )

            duration = time.time() - start_time

        # Display results
        if output_format == "json":
            result = {
                "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "calculation_duration": round(duration, 2),
                "implementation": "go" if is_go else "python",
                "algorithm": algorithm if is_go else "degree",
                "top_critical_nodes": top_critical_nodes,
            }

            # Add Python-specific data
            if not is_go:
                result["weights"] = {
                    "centrality_weight": scorer_instance.weights.centrality_weight,
                    "depth_weight": scorer_instance.weights.depth_weight,
                }
                result["cache_stats"] = scorer_instance.get_cache_stats()

            console.print(json.dumps(result, indent=2))
        else:
            # Display as rich table
            _display_criticality_table(
                console, top_critical_nodes, duration, scorer_instance, is_go
            )

    except CriticalityError as e:
        console.print(f"[red]Criticality analysis error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        logger.error(f"Failed to analyze criticality: {e}")
        raise click.Abort()


@criticality.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for criticality scores (default: stdout)",
)
@click.option(
    "--nodes-file", type=click.Path(exists=True), help="Path to nodes.json file"
)
@click.option(
    "--edges-file", type=click.Path(exists=True), help="Path to edges.json file"
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to criticality weights config file",
)
def export(
    output: Optional[str],
    nodes_file: Optional[str],
    edges_file: Optional[str],
    config: Optional[str],
):
    """Export criticality scores to JSON file."""
    console = Console()

    try:
        # Initialize scorer
        if config:
            scorer = CriticalityScorer.from_config_file(Path(config))
        else:
            scorer = CriticalityScorer()

        # Use default paths
        if nodes_file is None:
            nodes_file = str(PathResolver.nodes_file())
        if edges_file is None:
            edges_file = str(PathResolver.edges_file())

        # Load data
        with console.status("[cyan]Loading knowledge graph data..."):
            with open(nodes_file, "r") as f:
                nodes = json.load(f)
            with open(edges_file, "r") as f:
                edges = json.load(f)

        # Calculate scores
        with console.status("[cyan]Calculating criticality scores..."):
            scores = scorer.calculate_criticality_scores(nodes, edges)

        # Prepare export data
        export_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "weights": {
                "centrality_weight": scorer.weights.centrality_weight,
                "depth_weight": scorer.weights.depth_weight,
                "entry_point_patterns": scorer.weights.entry_point_patterns,
            },
            "scores": scores,
            "statistics": {
                "total_nodes": len(scores),
                "max_score": max(scores.values()) if scores else 0.0,
                "avg_score": sum(scores.values()) / len(scores) if scores else 0.0,
            },
        }

        # Write output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)
            console.print(
                f"[green]Criticality scores exported to:[/green] {output_path}"
            )
        else:
            console.print(json.dumps(export_data, indent=2))

    except Exception as e:
        console.print(f"[red]Export failed:[/red] {e}")
        logger.error(f"Failed to export criticality scores: {e}")
        raise click.Abort()


@criticality.command()
@click.option(
    "--output",
    "-o",
    default="criticality_weights.yaml",
    help="Output file for tuned weights",
)
@click.option(
    "--nodes-file", type=click.Path(exists=True), help="Path to nodes.json file"
)
@click.option(
    "--edges-file", type=click.Path(exists=True), help="Path to edges.json file"
)
@click.option(
    "--test-correlation", is_flag=True, help="Tune weights based on test correlation"
)
def tune(
    output: str,
    nodes_file: Optional[str],
    edges_file: Optional[str],
    test_correlation: bool,
):
    """Tune criticality weights for optimal results."""
    console = Console()

    try:
        # For now, provide a basic tuning approach
        # Future versions could implement more sophisticated optimization

        console.print("[yellow]Weight tuning is currently basic.[/yellow]")
        console.print("Consider these guidelines for manual tuning:")

        guidelines = [
            ("centrality_weight", "0.7", "Good for highly interconnected codebases"),
            ("depth_weight", "0.3", "Good for deep call hierarchies"),
            ("centrality_weight", "0.5", "Balanced for mixed architectures"),
            ("depth_weight", "0.5", "Balanced for mixed architectures"),
        ]

        table = Table(title="Weight Tuning Guidelines")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Best For", style="white")

        for param, value, description in guidelines:
            table.add_row(param, value, description)

        console.print(table)

        # Create a sample tuned config
        tuned_config = {
            "centrality_weight": 0.6,
            "depth_weight": 0.4,
            "entry_point_patterns": [
                "main",
                "test_*",
                "*_handler",
                "*_endpoint",
                "*_view",
                "handle_*",
                "*_main",
                "run_*",
            ],
            "normalization": {"max_call_depth": 25, "min_graph_size": 5},
            "performance": {
                "enable_caching": True,
                "auto_invalidate_cache": True,
                "max_batch_size": 1000,
            },
            "debug": {"verbose_logging": False, "export_intermediate_data": False},
        }

        # Write tuned config
        import yaml

        output_path = Path(output)
        with open(output_path, "w") as f:
            yaml.dump(tuned_config, f, default_flow_style=False, indent=2)

        console.print(
            f"\n[green]Sample tuned configuration written to:[/green] {output_path}"
        )
        console.print(
            "[yellow]Review and adjust weights based on your codebase characteristics.[/yellow]"
        )

    except Exception as e:
        console.print(f"[red]Tuning failed:[/red] {e}")
        logger.error(f"Failed to tune weights: {e}")
        raise click.Abort()


def _format_node_display(node: Dict[str, Any]) -> str:
    """Format node information for readable display."""
    node_name = node.get("node_name", node.get("name", "unknown"))
    file_path = node.get("file_path", "")
    node_type = node.get("type", "")

    if node_type == "Module":
        # For modules, show just the filename
        if file_path:
            return file_path.split("/")[-1].replace(".py", "")
        return node_name
    elif node_type == "Implementation":
        # For functions/methods, show file::function format
        if file_path and node_name:
            # Get last 2 path components for better readability
            path_parts = file_path.split("/")
            if len(path_parts) >= 2:
                short_path = "/".join(path_parts[-2:])
            else:
                short_path = path_parts[-1]

            # Remove .py extension
            short_path = short_path.replace(".py", "")
            return f"{short_path}::{node_name}"
        return node_name
    else:
        return node_name


def _get_node_type_display(node: Dict[str, Any]) -> str:
    """Get displayable node type with additional context."""
    node_type = node.get("type", node.get("node_type", "unknown"))

    # Check for additional context from properties
    if node_type == "Implementation":
        # Check if it's a test fixture or special type
        decorators = node.get("properties", {}).get("decorators", [])
        chunk_type = node.get("properties", {}).get("chunk_type", "")

        if any("@pytest.fixture" in dec for dec in decorators):
            return "fixture"
        elif chunk_type == "method":
            return "method"
        elif chunk_type == "function":
            return "function"
        else:
            return "impl"
    elif node_type == "Module":
        return "module"
    else:
        return str(node_type).lower()


def _get_location_display(node: Dict[str, Any]) -> str:
    """Get location information for display."""
    line_number = node.get("line_number")
    start_line = node.get("properties", {}).get("start_line")
    end_line = node.get("properties", {}).get("end_line")

    if line_number:
        return f"L{line_number}"
    elif start_line and end_line:
        if start_line == end_line:
            return f"L{start_line}"
        else:
            return f"L{start_line}-{end_line}"
    else:
        return "-"


def _display_criticality_table(
    console: Console,
    top_nodes: List[Dict[str, Any]],
    duration: float,
    scorer: Any,
    is_go: bool,
) -> None:
    """Display criticality results in a rich table."""

    # Create results table with enhanced columns
    table = Table(title="Top Critical Components")
    table.add_column("Rank", style="cyan", justify="right", width=4)
    table.add_column("Function/Module", style="white", min_width=30, max_width=60)
    table.add_column("Type", style="yellow", width=12)
    table.add_column("Score", style="green", justify="right", width=8)
    table.add_column("Location", style="dim", width=15)

    # Add rows for each node
    for i, node in enumerate(top_nodes[:20], 1):  # Limit to first 20 for display
        if isinstance(node, dict):
            # Enhanced formatting
            formatted_name = _format_node_display(node)
            node_type = _get_node_type_display(node)
            score = node.get("score", 0.0)
            location = _get_location_display(node)

            table.add_row(str(i), formatted_name, node_type, f"{score:.4f}", location)

    # Create summary panel
    implementation = "Go" if is_go else "Python"
    stats_panel = Panel(
        f"[bold]Analysis Duration:[/bold] {duration:.2f}s\n"
        f"[bold]Implementation:[/bold] {implementation}\n"
        f"[bold]Total Nodes Scored:[/bold] {len(top_nodes)}",
        title="Summary",
        border_style="blue",
    )

    # Display all components
    console.print(table)
    console.print(stats_panel)
