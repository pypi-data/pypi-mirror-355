"""
TestIndex cache command.

This module implements the `testindex cache` command for managing
the micro cache layer and monitoring performance.
"""

import json
import time
from typing import Dict, Optional, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


from aston.core.cli.runner import common_options
from aston.core.logging import get_logger
from aston.storage.cache.micro_cache import (
    get_micro_cache,
    clear_global_cache,
    CacheConfig,
)
from aston.storage.cache.graph_loader import load_and_warm_cache


logger = get_logger(__name__)


def output_cache_status(stats: Dict[str, Any]) -> None:
    """Output cache status as a rich table."""
    console = Console()

    # Performance stats
    perf = stats.get("performance", {})
    config = stats.get("config", {})
    memory = stats.get("memory_usage", {})
    state = stats.get("state", {})

    # Create status table
    table = Table(title="Micro Cache Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")

    # Hit ratio
    hit_ratio = perf.get("hit_ratio", 0)
    hit_status = (
        "🟢 Excellent" if hit_ratio > 0.8 else "🟡 Good" if hit_ratio > 0.5 else "🔴 Poor"
    )
    table.add_row("Hit Ratio", f"{hit_ratio:.1%}", hit_status)

    # Latency
    avg_latency = perf.get("avg_response_time_ms", 0)
    latency_target = config.get("target_latency_ms", 300)
    latency_status = "🟢 Fast" if avg_latency <= latency_target else "🔴 Slow"
    table.add_row("Avg Latency", f"{avg_latency:.2f}ms", latency_status)

    # Memory usage
    nodes_cached = memory.get("nodes_cached", 0)
    edges_cached = memory.get("edges_cached", 0)
    metrics_cached = memory.get("metrics_cached", 0)

    table.add_row("Nodes Cached", str(nodes_cached), "")
    table.add_row("Edges Cached", str(edges_cached), "")
    table.add_row("Metrics Cached", str(metrics_cached), "")

    # Request counts
    total_requests = perf.get("total_requests", 0)
    hits = perf.get("hits", 0)
    misses = perf.get("misses", 0)

    table.add_row("Total Requests", str(total_requests), "")
    table.add_row("Cache Hits", str(hits), "")
    table.add_row("Cache Misses", str(misses), "")

    # Pre-compute performance
    precompute_ratio = perf.get("precompute_hit_ratio", 0)
    precompute_status = (
        "🟢 Good"
        if precompute_ratio > 0.7
        else "🟡 Fair"
        if precompute_ratio > 0.3
        else "🔴 Poor"
    )
    table.add_row("Pre-compute Hit Ratio", f"{precompute_ratio:.1%}", precompute_status)

    # Cache state
    is_warmed = state.get("is_warmed_up", False)
    is_global = state.get("is_global_instance", False)

    table.add_row(
        "Cache Warmed", "Yes" if is_warmed else "No", "🟢" if is_warmed else "🔴"
    )
    table.add_row(
        "Global Instance", "Yes" if is_global else "No", "🟢" if is_global else "🟡"
    )

    # Overall status
    target_met = stats.get("latency_target_met", False)
    overall_status = (
        "🟢 Optimal"
        if target_met and hit_ratio > 0.7
        else "🟡 Good"
        if target_met
        else "🔴 Needs Attention"
    )
    table.add_row(
        "Overall Status",
        "Target Met" if target_met else "Target Missed",
        overall_status,
    )

    console.print()
    console.print(table)
    console.print()


def output_cache_config(config: Dict[str, Any]) -> None:
    """Output cache configuration."""
    console = Console()

    config_data = config.get("config", {})

    # Create config table
    table = Table(title="Cache Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Target Latency", f"{config_data.get('target_latency_ms', 300)}ms")
    table.add_row("Default TTL", f"{config_data.get('default_ttl_seconds', 3600)}s")
    table.add_row("Max Memory", f"{config_data.get('max_memory_mb', 512)}MB")
    table.add_row(
        "Pre-compute Threshold", str(config_data.get("precompute_threshold", 100))
    )

    # Feature flags
    features = []
    if config_data.get("enable_criticality_precompute", False):
        features.append("Criticality Pre-compute")
    if config_data.get("enable_centrality_precompute", False):
        features.append("Centrality Pre-compute")
    if config_data.get("enable_coverage_precompute", False):
        features.append("Coverage Pre-compute")

    table.add_row("Enabled Features", ", ".join(features) if features else "None")

    console.print(table)
    console.print()


def load_config() -> Dict[str, Any]:
    """Load configuration for cache operations."""
    try:
        from aston.cli.commands.coverage import load_config as load_coverage_config

        return load_coverage_config()
    except Exception as e:
        logger.warning(f"Failed to load config: {e}")
        return {"offline_mode": True}


@click.command("status", help="Display cache status and performance metrics")
@click.option(
    "--json", "json_output", type=click.Path(), help="Path to write JSON status output"
)
@click.option("--detailed", is_flag=True, help="Show detailed performance breakdown")
@common_options
def cache_status_command(
    json_output: Optional[str], detailed: bool, verbose: bool = False, **kwargs
):
    """Display cache status and performance metrics."""
    console = Console()

    try:
        # Get cache instance
        cache = get_micro_cache()
        stats = cache.get_cache_statistics()

        if json_output:
            # Write JSON output
            with open(json_output, "w") as f:
                json.dump(stats, f, indent=2)
            console.print(f"[green]Cache status written to {json_output}[/green]")
        else:
            # Display status
            output_cache_status(stats)

            if detailed:
                output_cache_config(stats)

        # Performance recommendations
        perf = stats.get("performance", {})
        recommendations = []

        if perf.get("hit_ratio", 0) < 0.5:
            recommendations.append(
                "Consider warming up the cache with `aston cache warm-up`"
            )

        if perf.get("avg_response_time_ms", 0) > 300:
            recommendations.append(
                "High latency detected. Check for slow data sources or increase cache size"
            )

        if perf.get("precompute_hit_ratio", 0) < 0.3:
            recommendations.append(
                "Enable pre-computation for frequently accessed metrics"
            )

        if recommendations:
            rec_text = "\n".join(f"• {rec}" for rec in recommendations)
            panel = Panel(
                rec_text, title="Performance Recommendations", border_style="yellow"
            )
            console.print(panel)

    except Exception as e:
        logger.error(f"Failed to get cache status: {e}")
        raise click.ClickException(f"Failed to get cache status: {e}")


@click.command("warm-up", help="Pre-populate cache with graph data")
@click.option(
    "--force", is_flag=True, help="Force cache refresh even if already warmed"
)
@click.option("--progress", is_flag=True, help="Show progress bar during warm-up")
@common_options
def cache_warmup_command(force: bool, progress: bool, verbose: bool = False, **kwargs):
    """Pre-populate cache with graph data."""
    console = Console()

    try:
        config = load_config()

        # Clear cache if forced
        if force:
            clear_global_cache()
            console.print("[yellow]Cleared existing cache[/yellow]")

        # Set up cache config for optimal warm-up
        cache_config = CacheConfig(
            target_latency_ms=300,
            enable_criticality_precompute=True,
            precompute_threshold=50,  # Lower threshold for warm-up
            log_slow_queries=verbose,
        )

        # Warm up cache
        start_time = time.time()

        if progress:
            console.print("[blue]Warming up cache...[/blue]")
            # Simulate progress for user feedback
            for _ in track(range(10), description="Loading graph data..."):
                time.sleep(0.1)

        cache = load_and_warm_cache(config, cache_config, force_reload=force)

        duration = time.time() - start_time
        stats = cache.get_cache_statistics()

        # Show results
        memory = stats.get("memory_usage", {})
        nodes_cached = memory.get("nodes_cached", 0)
        edges_cached = memory.get("edges_cached", 0)
        metrics_cached = memory.get("metrics_cached", 0)

        console.print(f"[green]✓ Cache warm-up completed in {duration:.2f}s[/green]")
        console.print(f"[green]  • {nodes_cached} nodes cached[/green]")
        console.print(f"[green]  • {edges_cached} edges cached[/green]")
        console.print(f"[green]  • {metrics_cached} metrics pre-computed[/green]")

        # Performance verification
        perf = stats.get("performance", {})
        avg_latency = perf.get("avg_response_time_ms", 0)
        if avg_latency <= 300:
            console.print(
                f"[green]🎯 Latency target met: {avg_latency:.2f}ms ≤ 300ms[/green]"
            )
        else:
            console.print(
                f"[yellow]⚠ Latency target missed: {avg_latency:.2f}ms > 300ms[/yellow]"
            )

    except Exception as e:
        logger.error(f"Failed to warm up cache: {e}")
        raise click.ClickException(f"Failed to warm up cache: {e}")


@click.command("clear", help="Clear all cached data")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@common_options
def cache_clear_command(confirm: bool, verbose: bool = False, **kwargs):
    """Clear all cached data."""
    console = Console()

    if not confirm:
        if not click.confirm("Are you sure you want to clear all cached data?"):
            console.print("[yellow]Cache clear cancelled[/yellow]")
            return

    try:
        clear_global_cache()
        console.print("[green]✓ Cache cleared successfully[/green]")

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise click.ClickException(f"Failed to clear cache: {e}")


# Main cache command group
@click.group("cache", help="Manage micro cache layer for sub-300ms performance")
@common_options
def cache_group(**kwargs):
    """Manage micro cache layer for sub-300ms performance."""
    pass


# Add subcommands
cache_group.add_command(cache_status_command)
cache_group.add_command(cache_warmup_command)
cache_group.add_command(cache_clear_command)
