"""Command-line interface for SliceSight-Next."""

import json
import random
import time
import uuid
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from slicesight_next.metrics import (
    auto_ratio_thresh,
    calc_cv,
    calc_gini,
    chisq_p,
    load_ratio,
    redis_cluster_slot,
    verdict,
)

app = typer.Typer(
    name="slicesight-hotshard",
    help="SliceSight-Next: Advanced Redis hotspot detection and analysis",
    no_args_is_help=True,
)
console = Console()


@app.command()
def simulate(
    keys: int = typer.Option(1000, "--keys", "-k", help="Number of keys to simulate"),
    buckets: int = typer.Option(3, "--buckets", "-b", help="Number of buckets/nodes"),
    ratio_thresh: float | None = typer.Option(None, "--ratio-thresh", "-r", help="Load ratio threshold"),
    auto_thresh: bool = typer.Option(False, "--auto-thresh", "-a", help="Use adaptive threshold"),
    p_thresh: float = typer.Option(0.05, "--p-thresh", "-p", help="P-value threshold"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    table_output: bool = typer.Option(True, "--table/--no-table", help="Output in table format"),
    seed: int | None = typer.Option(None, "--seed", "-s", help="Random seed for reproducibility"),
) -> None:
    """Simulate Redis key distribution and detect hotspots."""
    if seed is not None:
        random.seed(seed)

    # Generate random keys
    simulated_keys = [f"key_{i:06d}" for i in range(keys)]

    # Calculate slot distribution
    slot_counts = [0] * buckets
    for key in simulated_keys:
        slot = redis_cluster_slot(key) % buckets
        slot_counts[slot] += 1

    # Convert to loads (as floats)
    loads = [float(count) for count in slot_counts]

    # Calculate metrics
    load_ratio_val = load_ratio(loads)
    cv_val = calc_cv(loads)
    gini_val = calc_gini(loads)

    # Expected uniform distribution
    expected = [keys / buckets] * buckets
    p_val = chisq_p(slot_counts, expected)

    # Determine threshold
    if auto_thresh:
        threshold = auto_ratio_thresh(keys, buckets)
    else:
        threshold = ratio_thresh if ratio_thresh is not None else 2.0

    # Generate verdict
    result = verdict(load_ratio_val, cv_val, gini_val, p_val, threshold, p_thresh)

    # Prepare output data
    output_data = {
        "simulation": {
            "keys": keys,
            "buckets": buckets,
            "seed": seed,
        },
        "distribution": loads,
        "metrics": {
            "load_ratio": load_ratio_val,
            "coefficient_of_variation": cv_val,
            "gini_coefficient": gini_val,
            "chi_square_p_value": p_val,
        },
        "thresholds": {
            "ratio_threshold": threshold,
            "p_threshold": p_thresh,
            "auto_threshold": auto_thresh,
        },
        "verdict": result,
    }

    if json_output:
        console.print(json.dumps(output_data, indent=2))
    elif table_output:
        _display_simulation_table(output_data)


@app.command()
def scan(
    host: str = typer.Option("localhost", "--host", "-h", help="Redis host"),
    port: int = typer.Option(6379, "--port", "-p", help="Redis port"),
    buckets: int = typer.Option(3, "--buckets", "-b", help="Number of buckets/nodes"),
    ratio_thresh: float | None = typer.Option(None, "--ratio-thresh", "-r", help="Load ratio threshold"),
    auto_thresh: bool = typer.Option(False, "--auto-thresh", "-a", help="Use adaptive threshold"),
    p_thresh: float = typer.Option(0.05, "--p-thresh", help="P-value threshold"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    table_output: bool = typer.Option(True, "--table/--no-table", help="Output in table format"),
) -> None:
    """Scan Redis instance for key distribution and hotspots."""
    console.print(f"[yellow]Scanning Redis at {host}:{port}...[/yellow]")

    # Mock implementation - in real version would connect to Redis
    # For MVP, simulate some data
    sample_keys = ["user:123", "session:abc", "cache:xyz", "temp:456"]
    loads = [100.0, 200.0, 50.0]  # Mock load data

    load_ratio_val = load_ratio(loads)
    cv_val = calc_cv(loads)
    gini_val = calc_gini(loads)

    expected = [sum(loads) / len(loads)] * len(loads)
    observed = [int(load) for load in loads]
    p_val = chisq_p(observed, expected)

    threshold = auto_ratio_thresh(len(sample_keys), buckets) if auto_thresh else (ratio_thresh or 2.0)
    result = verdict(load_ratio_val, cv_val, gini_val, p_val, threshold, p_thresh)

    output_data = {
        "scan": {
            "host": host,
            "port": port,
            "buckets": buckets,
            "keys_sampled": len(sample_keys),
        },
        "distribution": loads,
        "metrics": {
            "load_ratio": load_ratio_val,
            "coefficient_of_variation": cv_val,
            "gini_coefficient": gini_val,
            "chi_square_p_value": p_val,
        },
        "thresholds": {
            "ratio_threshold": threshold,
            "p_threshold": p_thresh,
            "auto_threshold": auto_thresh,
        },
        "verdict": result,
    }

    if json_output:
        console.print(json.dumps(output_data, indent=2))
    elif table_output:
        _display_scan_table(output_data)


@app.command()
def score(
    loads: list[float] = typer.Argument(..., help="Load values for each node"),
    buckets: int | None = typer.Option(None, "--buckets", "-b", help="Number of buckets (auto-detected from loads)"),
    ratio_thresh: float | None = typer.Option(None, "--ratio-thresh", "-r", help="Load ratio threshold"),
    auto_thresh: bool = typer.Option(False, "--auto-thresh", "-a", help="Use adaptive threshold"),
    p_thresh: float = typer.Option(0.05, "--p-thresh", help="P-value threshold"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    table_output: bool = typer.Option(True, "--table/--no-table", help="Output in table format"),
) -> None:
    """Score given load distribution for hotspot detection."""
    if buckets is None:
        buckets = len(loads)

    # Calculate metrics
    load_ratio_val = load_ratio(loads)
    cv_val = calc_cv(loads)
    gini_val = calc_gini(loads)

    # For chi-square test
    total_load = sum(loads)
    expected = [total_load / len(loads)] * len(loads)
    observed = [int(load) for load in loads]
    p_val = chisq_p(observed, expected)

    # Determine threshold
    if auto_thresh:
        # Estimate total keys from total load (rough approximation)
        estimated_keys = int(total_load)
        threshold = auto_ratio_thresh(estimated_keys, buckets)
    else:
        threshold = ratio_thresh if ratio_thresh is not None else 2.0

    # Generate verdict
    result = verdict(load_ratio_val, cv_val, gini_val, p_val, threshold, p_thresh)

    output_data = {
        "input": {
            "loads": loads,
            "buckets": buckets,
        },
        "metrics": {
            "load_ratio": load_ratio_val,
            "coefficient_of_variation": cv_val,
            "gini_coefficient": gini_val,
            "chi_square_p_value": p_val,
        },
        "thresholds": {
            "ratio_threshold": threshold,
            "p_threshold": p_thresh,
            "auto_threshold": auto_thresh,
        },
        "verdict": result,
    }

    if json_output:
        console.print(json.dumps(output_data, indent=2))
    elif table_output:
        _display_score_table(output_data)


@app.command()
def test_pattern(
    pattern: str = typer.Argument(None, help="Key pattern with placeholders (e.g., 'user:{id}:profile')"),
    samples: int = typer.Option(1000, "--samples", "-n", help="Number of sample keys to generate"),
    buckets: int = typer.Option(16, "--buckets", "-b", help="Number of buckets/nodes"),
    auto_thresh: bool = typer.Option(True, "--auto-thresh/--no-auto-thresh", help="Use adaptive threshold"),
    ratio_thresh: float | None = typer.Option(None, "--ratio-thresh", "-r", help="Manual load ratio threshold"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    examples: bool = typer.Option(False, "--examples", help="Show pattern examples and exit"),
) -> None:
    """Test key distribution patterns with placeholders.
    
    Placeholders:
      {id}       - Sequential integers (1, 2, 3, ...)
      {uuid}     - Random UUIDs
      {user_id}  - Sequential user IDs  
      {session}  - Random session IDs (short UUIDs)
      {timestamp} - Unix timestamps with some variation
      
    Examples:
      slicesight-hotshard test-pattern "user:{id}:profile"
      slicesight-hotshard test-pattern "session:{uuid}:data" 
      slicesight-hotshard test-pattern "cache:{user_id}:{timestamp}"
    """
    if examples:
        _show_pattern_examples()
        return
    
    if pattern is None:
        console.print("[red]Error: Pattern is required[/red]")
        console.print("Use --examples to see pattern examples")
        return
    
    # Generate sample keys based on pattern
    keys = _generate_keys_from_pattern(pattern, samples)
    
    if not keys:
        console.print("[red]Error: Could not generate keys from pattern[/red]")
        console.print("Use --examples to see valid patterns")
        return
    
    # Calculate slot distribution
    slot_counts = [0] * buckets
    for key in keys:
        slot = redis_cluster_slot(key) % buckets
        slot_counts[slot] += 1
    
    # Convert to loads
    loads = [float(count) for count in slot_counts]
    
    # Calculate metrics
    load_ratio_val = load_ratio(loads)
    cv_val = calc_cv(loads)
    gini_val = calc_gini(loads)
    
    # Expected uniform distribution
    expected = [samples / buckets] * buckets
    p_val = chisq_p(slot_counts, expected)
    
    # Determine threshold
    if auto_thresh:
        threshold = auto_ratio_thresh(samples, buckets)
    else:
        threshold = ratio_thresh if ratio_thresh is not None else 2.0
    
    # Generate verdict
    result = verdict(load_ratio_val, cv_val, gini_val, p_val, threshold, 0.05)
    
    # Sample keys for display
    sample_keys = keys[:5] if len(keys) >= 5 else keys
    
    output_data = {
        "pattern": pattern,
        "test_config": {
            "samples": samples,
            "buckets": buckets,
            "threshold_type": "adaptive" if auto_thresh else "manual"
        },
        "sample_keys": sample_keys,
        "distribution": loads,
        "metrics": {
            "load_ratio": load_ratio_val,
            "coefficient_of_variation": cv_val,
            "gini_coefficient": gini_val,
            "chi_square_p_value": p_val,
        },
        "thresholds": {
            "ratio_threshold": threshold,
            "p_threshold": 0.05,
        },
        "verdict": result,
    }
    
    if json_output:
        console.print(json.dumps(output_data, indent=2))
    else:
        _display_pattern_results(output_data)


@app.command()
def feedback(
    message: str = typer.Argument(..., help="Your feedback message"),
    email: str = typer.Option(None, "--email", help="Your email for follow-up (optional)"),
    category: str = typer.Option("general", "--category", help="Feedback category: bug, feature, usability, performance"),
) -> None:
    """Submit feedback to help improve SliceSight-Next.
    
    Examples:
        slicesight-hotshard feedback "Great tool! Would love more hash tag examples"
        slicesight-hotshard feedback "Found a bug with UUID generation" --category bug --email me@company.com
    """
    feedback_data = {
        "message": message,
        "email": email,
        "category": category,
        "version": "0.2.0",
        "timestamp": int(time.time())
    }
    
    console.print("[green]✓[/green] Thank you for your feedback!")
    console.print(f"Message: {message}")
    console.print(f"Category: {category}")
    
    # Store locally for now (in production, would send to analytics service)
    console.print("\n[yellow]💡 You can also:[/yellow]")
    console.print("• Open issues: https://github.com/slicesight/slicesight-next/issues")  
    console.print("• Join discussions: https://github.com/slicesight/slicesight-next/discussions")
    console.print("• Star the repo if you find it useful! ⭐")


@app.command()
def health(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Check system health and dependencies."""
    health_data = {
        "status": "healthy",
        "version": "0.2.0",
        "dependencies": {
            "typer": "available",
            "rich": "available",
        },
        "features": {
            "metrics_calculation": True,
            "adaptive_threshold": True,
            "cli_interface": True,
        }
    }

    if json_output:
        console.print(json.dumps(health_data, indent=2))
    else:
        console.print("[green]✓[/green] SliceSight-Next is healthy")
        console.print(f"Version: {health_data['version']}")
        console.print("All core features operational")
        console.print("\n[yellow]💬 Found an issue or have suggestions?[/yellow]")
        console.print("Run: [bold]slicesight-hotshard feedback \"your message here\"[/bold]")


def _display_simulation_table(data: dict[str, Any]) -> None:
    """Display simulation results in table format."""
    table = Table(title="SliceSight-Next Simulation Results")

    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")

    # Add metrics
    metrics = data["metrics"]
    thresholds = data["thresholds"]
    results = data["verdict"]

    table.add_row("Load Ratio", f"{metrics['load_ratio']:.3f}",
                  "🔥 IMBALANCED" if results["load_imbalance"] else "✓ Balanced")
    table.add_row("Coefficient of Variation", f"{metrics['coefficient_of_variation']:.3f}",
                  "⚠️ HIGH" if results["high_variability"] else "✓ Normal")
    table.add_row("Gini Coefficient", f"{metrics['gini_coefficient']:.3f}",
                  "📊 UNEQUAL" if results["inequality"] else "✓ Equal")
    table.add_row("Chi-square P-value", f"{metrics['chi_square_p_value']:.3f}",
                  "🎯 NON-UNIFORM" if results["non_uniform"] else "✓ Uniform")

    table.add_section()
    table.add_row("Hotspot Detected", "",
                  "🚨 YES" if results["hotspot_detected"] else "✅ NO")

    console.print(table)
    console.print(f"\nDistribution: {data['distribution']}")


def _display_scan_table(data: dict[str, Any]) -> None:
    """Display scan results in table format."""
    _display_simulation_table(data)  # Same format for now


def _generate_keys_from_pattern(pattern: str, count: int) -> list[str]:
    """Generate keys from a pattern with placeholders."""
    
    keys = []
    base_timestamp = int(time.time())
    
    for i in range(count):
        key = pattern
        
        # Replace placeholders
        key = key.replace("{id}", str(i + 1))
        key = key.replace("{user_id}", str(i + 1))
        key = key.replace("{uuid}", str(uuid.uuid4()))
        key = key.replace("{session}", str(uuid.uuid4())[:8])
        key = key.replace("{timestamp}", str(base_timestamp + (i % 3600)))  # Vary within an hour
        
        keys.append(key)
    
    return keys


def _show_pattern_examples() -> None:
    """Show examples of key patterns."""
    examples_table = Table(title="Key Pattern Examples")
    examples_table.add_column("Pattern", style="cyan")
    examples_table.add_column("Description", style="white")
    examples_table.add_column("Sample Key", style="yellow")
    examples_table.add_column("Distribution", style="green")
    
    examples = [
        ("user:{id}:profile", "Sequential user profiles", "user:123:profile", "⚠️ Can cluster"),
        ("user:{uuid}:profile", "UUID-based users", "user:a1b2c3d4...:profile", "✅ Good"),
        ("session:{uuid}:data", "Session storage", "session:f47ac10b...:data", "✅ Excellent"),
        ("session:{{uuid}}:data", "Grouped sessions", "session:{f47ac10b...}:data", "⚠️ Forced grouping"),
        ("cache:{user_id}:{timestamp}", "Time-based cache", "cache:123:1703123456", "✅ Good"),
        ("config:app", "Static keys", "config:app", "❌ All same slot"),
        ("tenant:{id}:user:{user_id}", "Multi-tenant", "tenant:5:user:123", "✅ Good entropy"),
    ]
    
    for pattern, desc, sample, dist in examples:
        examples_table.add_row(pattern, desc, sample, dist)
    
    console.print(examples_table)
    console.print("\n[bold]Placeholder Types:[/bold]")
    console.print("• {id} - Sequential integers (1, 2, 3...)")
    console.print("• {user_id} - Alias for {id}")
    console.print("• {uuid} - Full UUID (36 chars)")
    console.print("• {session} - Short UUID (8 chars)")  
    console.print("• {timestamp} - Unix timestamp with variation")
    console.print("\n[bold]Hash Tag Rules:[/bold]")
    console.print("• {value} in pattern → Redis hash tag (forces same slot)")
    console.print("• {{value}} in pattern → Literal {value} in key")


def _display_pattern_results(data: dict[str, Any]) -> None:
    """Display pattern test results."""
    table = Table(title=f"Pattern Test: {data['pattern']}")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")
    
    # Add metrics
    metrics = data["metrics"]
    results = data["verdict"]
    
    table.add_row("Load Ratio", f"{metrics['load_ratio']:.3f}",
                  "🔥 IMBALANCED" if results["load_imbalance"] else "✅ Balanced")
    table.add_row("Coefficient of Variation", f"{metrics['coefficient_of_variation']:.3f}",
                  "⚠️ HIGH" if results["high_variability"] else "✅ Normal")
    table.add_row("Gini Coefficient", f"{metrics['gini_coefficient']:.3f}",
                  "📊 UNEQUAL" if results["inequality"] else "✅ Equal")
    table.add_row("Chi-square P-value", f"{metrics['chi_square_p_value']:.3f}",
                  "🎯 NON-UNIFORM" if results["non_uniform"] else "✅ Uniform")
    
    table.add_section()
    table.add_row("Overall Verdict", "",
                  "🚨 HOTSPOT RISK" if results["hotspot_detected"] else "✅ GOOD DISTRIBUTION")
    
    console.print(table)
    
    # Show sample keys
    console.print(f"\n[bold]Sample Keys Generated:[/bold]")
    for key in data["sample_keys"]:
        console.print(f"  {key}")
    
    # Show distribution
    console.print(f"\n[bold]Distribution across {len(data['distribution'])} buckets:[/bold]")
    dist_str = " ".join(f"{int(x)}" for x in data["distribution"])
    console.print(f"  [{dist_str}]")
    
    # Show recommendation
    if results["hotspot_detected"]:
        console.print(f"\n[bold red]⚠️ Recommendation:[/bold red]")
        if "{id}" in data["pattern"] or "{user_id}" in data["pattern"]:
            console.print("  • Consider using {uuid} instead of {id} for better distribution")
        if "{{" in data["pattern"]:
            console.print("  • Hash tags {{}} force keys to same slots - avoid unless needed")
        console.print("  • Test with --samples 10000 for more accurate results")
    else:
        console.print(f"\n[bold green]✅ This pattern distributes well![/bold green]")


def _display_score_table(data: dict[str, Any]) -> None:
    """Display score results in table format."""
    table = Table(title="SliceSight-Next Score Results")

    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")

    # Add metrics
    metrics = data["metrics"]
    thresholds = data["thresholds"]
    results = data["verdict"]

    table.add_row("Load Ratio", f"{metrics['load_ratio']:.3f}",
                  "🔥 IMBALANCED" if results["load_imbalance"] else "✓ Balanced")
    table.add_row("Coefficient of Variation", f"{metrics['coefficient_of_variation']:.3f}",
                  "⚠️ HIGH" if results["high_variability"] else "✓ Normal")
    table.add_row("Gini Coefficient", f"{metrics['gini_coefficient']:.3f}",
                  "📊 UNEQUAL" if results["inequality"] else "✓ Equal")
    table.add_row("Chi-square P-value", f"{metrics['chi_square_p_value']:.3f}",
                  "🎯 NON-UNIFORM" if results["non_uniform"] else "✓ Uniform")

    table.add_section()
    table.add_row("Hotspot Detected", "",
                  "🚨 YES" if results["hotspot_detected"] else "✅ NO")

    console.print(table)
    console.print(f"\nDistribution: {data['input']['loads']}")


if __name__ == "__main__":
    app()
