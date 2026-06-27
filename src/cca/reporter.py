"""Rich-based terminal output."""
from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cca.parser import FileInfo

# Non-ASCII chars are intentionally avoided in all output so Windows cp* encodings work.
console = Console(highlight=False)

_BAR_WIDTH = 30  # max bar length in chars


def _bar(value: int, max_value: int, width: int = _BAR_WIDTH) -> str:
    """Return a proportional ASCII bar string."""
    if max_value == 0:
        return ""
    filled = round(value / max_value * width)
    return "|" * filled + "." * (width - filled)


def print_analysis_table(
    file_infos: list[FileInfo],
    root: Path,
    in_degrees: dict[str, int],
    hot_files: dict[str, int],
) -> None:
    table = Table(
        title=f"Project Analysis - {root.name}",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("File", style="white", no_wrap=True, min_width=30)
    table.add_column("Lines", justify="right", style="yellow")
    table.add_column("Funcs", justify="right", style="green")
    table.add_column("Classes", justify="right", style="blue")
    table.add_column("Imports", justify="right", style="dim")
    table.add_column("Imported by", justify="right", style="bold red")
    table.add_column("Hot", justify="center", style="red")

    sorted_infos = sorted(
        file_infos,
        key=lambda f: in_degrees.get(str(f.path.relative_to(root)), 0),
        reverse=True,
    )

    for info in sorted_infos:
        rel = str(info.path.relative_to(root))
        imported_by = in_degrees.get(rel, 0)
        table.add_row(
            rel,
            str(info.lines),
            str(info.function_count),
            str(info.class_count),
            str(len(info.imports)),
            str(imported_by) if imported_by else "-",
            "HOT" if rel in hot_files else "",
        )

    console.print(table)


def print_dependency_summary(most_imported: list[tuple[str, int]]) -> None:
    top = [(p, c) for p, c in most_imported if c > 0][:5]
    if not top:
        return
    body = "\n".join(
        f"  [cyan]{p}[/cyan]  <-  imported by [bold]{c}[/bold] file{'s' if c != 1 else ''}"
        for p, c in top
    )
    console.print(Panel(body, title="[bold]Most Imported Files[/bold]", border_style="cyan"))


def print_before_after(baseline: int, optimized: int, savings_pct: float) -> None:
    """Two-line visual bar showing token count before vs after the tool."""
    bar_total = 50
    before_bar = "|" * bar_total
    after_filled = round(optimized / baseline * bar_total) if baseline else 0
    after_bar = "|" * after_filled + "." * (bar_total - after_filled)
    saved = baseline - optimized
    console.print(
        f"\n  [bold]UYGULAMASIZ[/bold]  [red]{before_bar}[/red]  [yellow]{baseline:>8,}[/yellow] token\n"
        f"  [bold]UYGULAMALI [/bold]  [green]{after_bar}[/green]  [green]{optimized:>8,}[/green] token\n"
        f"\n  [bold green]{savings_pct:.1f}% tasarruf[/bold green]  "
        f"([dim]{saved:,} token daha az Claude'a gidiyor[/dim])\n"
    )


def print_token_report(baseline: int, optimized: int, savings_pct: float) -> None:
    print_before_after(baseline, optimized, savings_pct)
    console.print(Panel(
        f"  Tum proje (ignore yok):    [yellow]{baseline:>10,}[/yellow] token\n"
        f"  .claudeignore ile:         [green]{optimized:>10,}[/green] token\n"
        f"  Tahmini tasarruf:          [bold green]{savings_pct:>9.1f}%[/bold green]",
        title="[bold]Token Butcesi[/bold]",
        subtitle="[dim]cl100k_base ile hesaplandi (~Claude tokenizer, +-10%)[/dim]",
        border_style="green",
    ))


def print_token_chart(file_tokens: dict[str, int], title: str = "Token Distribution per File") -> None:
    """Print a horizontal bar chart of token counts per file."""
    if not file_tokens:
        console.print("[dim]No files to chart.[/dim]")
        return

    sorted_items = sorted(file_tokens.items(), key=lambda x: x[1], reverse=True)
    max_tokens = sorted_items[0][1] if sorted_items else 1
    total = sum(file_tokens.values())

    table = Table(
        title=title,
        box=box.SIMPLE_HEAD,
        header_style="bold magenta",
        show_lines=False,
        padding=(0, 1),
    )
    table.add_column("File", style="white", no_wrap=True, min_width=35)
    table.add_column("Tokens", justify="right", style="yellow", min_width=7)
    table.add_column("Pct", justify="right", style="dim", min_width=5)
    table.add_column(f"Distribution (max={max_tokens:,})", style="cyan", min_width=_BAR_WIDTH + 2)

    for path, tokens in sorted_items:
        pct = tokens / total * 100 if total else 0
        bar = _bar(tokens, max_tokens)
        # Color the bar: high = red, medium = yellow, low = green
        if pct > 20:
            bar_markup = f"[red]{bar}[/red]"
        elif pct > 5:
            bar_markup = f"[yellow]{bar}[/yellow]"
        else:
            bar_markup = f"[green]{bar}[/green]"
        table.add_row(path, f"{tokens:,}", f"{pct:.1f}%", bar_markup)

    console.print(table)
    console.print(f"  [bold]Total: {total:,} tokens[/bold]  |  {len(file_tokens)} files\n")


def print_token_comparison_chart(baseline_files: dict[str, int], optimized_files: dict[str, int]) -> None:
    """Show a side-by-side comparison: what gets excluded by .claudeignore."""
    excluded = {k: v for k, v in baseline_files.items() if k not in optimized_files}
    included = optimized_files

    baseline_total = sum(baseline_files.values())
    optimized_total = sum(optimized_files.values())
    savings_pct = (baseline_total - optimized_total) / baseline_total * 100 if baseline_total else 0

    # Included files chart
    if included:
        print_token_chart(included, title="Included Files (after .claudeignore)")

    # Excluded summary
    if excluded:
        excluded_total = sum(excluded.values())
        top_excluded = sorted(excluded.items(), key=lambda x: x[1], reverse=True)[:8]

        table = Table(
            title="Excluded by .claudeignore (not sent to Claude)",
            box=box.SIMPLE_HEAD,
            header_style="bold red",
            show_lines=False,
            padding=(0, 1),
        )
        table.add_column("Path", style="dim", no_wrap=True, min_width=35)
        table.add_column("Tokens", justify="right", style="red", min_width=7)
        table.add_column("Bar", style="dim", min_width=_BAR_WIDTH + 2)

        max_excl = top_excluded[0][1] if top_excluded else 1
        for path, tokens in top_excluded:
            table.add_row(path, f"{tokens:,}", _bar(tokens, max_excl))

        if len(excluded) > 8:
            table.add_row(f"  ... and {len(excluded) - 8} more files", "", "")
        console.print(table)
        console.print(f"  [red]Excluded total: {excluded_total:,} tokens ({savings_pct:.1f}% of project)[/red]\n")


def print_quality_table(file_infos: list[FileInfo], root: Path) -> None:
    """Show cyclomatic complexity and type coverage per file."""
    if not file_infos:
        return

    total_funcs = sum(f.function_count for f in file_infos)
    total_typed = sum(f.typed_functions for f in file_infos)
    project_coverage = total_typed / total_funcs * 100 if total_funcs else 0.0

    table = Table(
        title="Code Quality Metrics",
        box=box.SIMPLE_HEAD,
        header_style="bold magenta",
        show_lines=False,
    )
    table.add_column("File", style="white", no_wrap=True, min_width=30)
    table.add_column("Complexity", justify="right", style="yellow")
    table.add_column("Type Cov.", justify="right", style="cyan")
    table.add_column("Grade", justify="center")

    sorted_infos = sorted(file_infos, key=lambda f: f.complexity, reverse=True)

    for info in sorted_infos:
        rel = str(info.path.relative_to(root))
        cov = f"{info.type_coverage:.0f}%"

        # complexity grade
        cx = info.complexity
        if cx <= 5:
            grade = "[green]A[/green]"
        elif cx <= 10:
            grade = "[yellow]B[/yellow]"
        elif cx <= 20:
            grade = "[red]C[/red]"
        else:
            grade = "[bold red]D[/bold red]"

        cx_style = "green" if cx <= 5 else ("yellow" if cx <= 10 else "red")
        table.add_row(rel, f"[{cx_style}]{cx}[/{cx_style}]", cov, grade)

    console.print(table)
    console.print(
        f"  Project type coverage: [bold cyan]{project_coverage:.1f}%[/bold cyan]  "
        f"([dim]{total_typed}/{total_funcs} functions annotated[/dim])\n"
    )


def print_cycles_warning(cycles: list[list[str]]) -> None:
    """Warn about circular import dependencies."""
    if not cycles:
        console.print(Panel(
            "[green]No circular dependencies found.[/green]",
            title="[bold]Circular Dependencies[/bold]",
            border_style="green",
        ))
        return

    lines = []
    for cycle in cycles[:8]:
        chain = " -> ".join(cycle) + f" -> {cycle[0]}"
        lines.append(f"  [red]{chain}[/red]")
    if len(cycles) > 8:
        lines.append(f"  [dim]... and {len(cycles) - 8} more[/dim]")

    console.print(Panel(
        "\n".join(lines),
        title=f"[bold red]Circular Dependencies ({len(cycles)} found)[/bold red]",
        subtitle="[dim]Circular imports cause hard-to-debug import errors[/dim]",
        border_style="red",
    ))


def print_frameworks(frameworks: dict[str, str]) -> None:
    """Show detected frameworks/libraries."""
    if not frameworks:
        return
    items = "  ".join(f"[cyan]{label}[/cyan]" for label in frameworks.values())
    console.print(Panel(items, title="[bold]Detected Frameworks[/bold]", border_style="blue"))


def print_health_score(score: "HealthScore") -> None:  # type: ignore[name-defined]
    """Display composite health score with a breakdown table."""
    grade_color = {"A": "bold green", "B": "green", "C": "yellow", "D": "red"}
    color = grade_color.get(score.grade, "white")
    total = score.total

    bar_width = 40
    filled = round(total / 100 * bar_width)
    bar = "|" * filled + "." * (bar_width - filled)
    bar_color = "green" if total >= 75 else ("yellow" if total >= 60 else "red")

    table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", show_lines=False)
    table.add_column("Metric", style="white", min_width=20)
    table.add_column("Score", justify="right", style="yellow", min_width=8)
    table.add_column("Weight", justify="right", style="dim", min_width=7)

    rows = [
        ("Token savings", score.token_savings, "30%"),
        ("Type coverage", score.type_coverage, "25%"),
        ("Complexity", score.complexity_score, "20%"),
        ("Dead code", score.dead_code_score, "15%"),
        ("No cycles", score.cycle_score, "10%"),
    ]
    for label, val, weight in rows:
        c = "green" if val >= 75 else ("yellow" if val >= 60 else "red")
        table.add_row(label, f"[{c}]{val:.0f}[/{c}]", weight)

    console.print(table)
    console.print(
        f"\n  [{bar_color}]{bar}[/{bar_color}]  [{color}]{total:.1f}/100 — Grade {score.grade}[/{color}]\n"
    )


def print_unused(unused: dict[str, list[str]]) -> None:
    if not unused:
        console.print(Panel("[green]No obvious dead code detected.[/green]", border_style="green"))
        return
    lines = [
        f"  [yellow]{path}[/yellow]  ->  {', '.join(syms)}"
        for path, syms in list(unused.items())[:12]
    ]
    console.print(Panel(
        "\n".join(lines),
        title="[bold yellow]Possible Dead Code[/bold yellow]",
        subtitle="[dim]Verify before removing - dynamic access not detected[/dim]",
        border_style="yellow",
    ))
