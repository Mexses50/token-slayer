"""Real-time Claude Code session token monitor."""
from __future__ import annotations

import json
import time
from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"

# Claude Sonnet 4.6 pricing (USD per token)
_PRICE_INPUT = 3.00 / 1_000_000
_PRICE_OUTPUT = 15.00 / 1_000_000
_PRICE_CACHE_WRITE = 3.75 / 1_000_000
_PRICE_CACHE_READ = 0.30 / 1_000_000


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def parse_session(jsonl_path: Path) -> dict:
    """Sum token usage from a Claude Code session JSONL (deduped by UUID)."""
    seen: set[str] = set()
    inp = out = cache_w = cache_r = turns = 0
    try:
        with jsonl_path.open(encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                uid = obj.get("uuid", "")
                if uid and uid in seen:
                    continue
                if uid:
                    seen.add(uid)
                usage = obj.get("message", {}).get("usage") or {}
                if not usage:
                    continue
                inp += usage.get("input_tokens", 0)
                out += usage.get("output_tokens", 0)
                cache_w += usage.get("cache_creation_input_tokens", 0)
                cache_r += usage.get("cache_read_input_tokens", 0)
                turns += 1
    except OSError:
        pass

    cost = inp * _PRICE_INPUT + out * _PRICE_OUTPUT + cache_w * _PRICE_CACHE_WRITE + cache_r * _PRICE_CACHE_READ
    return {
        "session_id": jsonl_path.stem,
        "short_id": jsonl_path.stem[:8],
        "project": jsonl_path.parent.name,
        "path": jsonl_path,
        "mtime": jsonl_path.stat().st_mtime if jsonl_path.exists() else 0,
        "input_tokens": inp,
        "output_tokens": out,
        "cache_write": cache_w,
        "cache_read": cache_r,
        "total_tokens": inp + out,
        "turns": turns,
        "cost_usd": round(cost, 5),
    }


def get_recent_sessions(hours: int = 24) -> list[dict]:
    """Return all sessions modified within the last N hours, newest first."""
    if not CLAUDE_PROJECTS.exists():
        return []
    cutoff = time.time() - hours * 3600
    sessions = [
        parse_session(p)
        for p in CLAUDE_PROJECTS.rglob("*.jsonl")
        if p.stat().st_mtime > cutoff
    ]
    return sorted(sessions, key=lambda s: s["mtime"], reverse=True)


def _make_session_panel(s: dict, highlight: str = "cyan") -> Panel:
    t = Table.grid(padding=(0, 1))
    t.add_column(style="dim", width=16)
    t.add_column(justify="right", style="bold")

    has_delta = s.get("delta_output", 0) > 0 or s.get("delta_input", 0) > 0

    if has_delta:
        t.add_row("[dim]── son mesaj ──[/dim]", "")
        t.add_row("Δ Input",  f"[green]+{_fmt(s['delta_input'])}[/green]")
        t.add_row("Δ Output", f"[yellow]+{_fmt(s['delta_output'])}[/yellow]")
        t.add_row("Δ Cache W", f"[blue]+{_fmt(s['delta_cache_w'])}[/blue]")
        t.add_row("Δ Cost",   f"[bold magenta]+${s['delta_cost']:.4f}[/bold magenta]")
        t.add_row("─" * 16, "─" * 8)

    t.add_row("[dim]── toplam ──[/dim]", "")
    t.add_row("Turns", str(s["turns"]))
    t.add_row("Input", f"[green]{_fmt(s['input_tokens'])}[/green]")
    t.add_row("Output", f"[yellow]{_fmt(s['output_tokens'])}[/yellow]")
    t.add_row("Cache write", f"[blue]{_fmt(s['cache_write'])}[/blue]")
    t.add_row("Cache read", f"[cyan]{_fmt(s['cache_read'])}[/cyan]")
    t.add_row("─" * 16, "─" * 8)
    t.add_row("Total", f"[bold]{_fmt(s['total_tokens'])}[/bold]")
    t.add_row("Cost", f"[bold magenta]${s['cost_usd']:.4f}[/bold magenta]")

    title = f"[{highlight}]{s['short_id']}[/{highlight}]"
    return Panel(t, title=title, border_style=highlight, expand=True)


def _make_full_table(sessions: list[dict]) -> Table:
    tbl = Table(
        title="[bold]Active Claude Code Sessions[/bold]",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        expand=True,
    )
    tbl.add_column("Session", style="cyan", no_wrap=True)
    tbl.add_column("Project", style="dim", max_width=24)
    tbl.add_column("Turns", justify="right")
    tbl.add_column("Input", justify="right", style="green")
    tbl.add_column("Output", justify="right", style="yellow")
    tbl.add_column("Cache W", justify="right", style="blue")
    tbl.add_column("Cache R", justify="right", style="cyan")
    tbl.add_column("Total", justify="right", style="bold")
    tbl.add_column("Cost $", justify="right", style="magenta")

    for s in sessions:
        tbl.add_row(
            s["short_id"],
            s["project"][:24],
            str(s["turns"]),
            _fmt(s["input_tokens"]),
            _fmt(s["output_tokens"]),
            _fmt(s["cache_write"]),
            _fmt(s["cache_read"]),
            _fmt(s["total_tokens"]),
            f"${s['cost_usd']:.4f}",
        )
    return tbl


def _compare_panel(a: dict, b: dict) -> Panel:
    """Side-by-side diff panel for two sessions."""
    def _diff_str(va: int, vb: int) -> str:
        diff = vb - va
        if diff > 0:
            return f"[red]+{_fmt(diff)}[/red]"
        if diff < 0:
            return f"[green]{_fmt(abs(diff))}[/green]"
        return "[dim]==[/dim]"

    t = Table.grid(padding=(0, 1))
    t.add_column(style="dim", width=14)
    t.add_column(justify="right", width=10)
    t.add_column(justify="center", width=10)
    t.add_column(justify="right", width=10)

    t.add_row("", f"[cyan]{a['short_id']}[/cyan]", "diff →", f"[yellow]{b['short_id']}[/yellow]")
    t.add_row("─" * 14, "─" * 10, "─" * 10, "─" * 10)

    has_delta = a.get("delta_output", 0) > 0 or b.get("delta_output", 0) > 0
    if has_delta:
        t.add_row("[dim]son mesaj[/dim]", "", "", "")
        for label, key in [("Δ Input", "delta_input"), ("Δ Output", "delta_output"),
                            ("Δ Cache W", "delta_cache_w")]:
            va, vb = a.get(key, 0), b.get(key, 0)
            t.add_row(label, _fmt(va), _diff_str(va, vb), _fmt(vb))
        ca, cb = a.get("delta_cost", 0.0), b.get("delta_cost", 0.0)
        t.add_row("Δ Cost $", f"${ca:.4f}", _diff_str(int(ca * 10000), int(cb * 10000)), f"${cb:.4f}")
        t.add_row("─" * 14, "─" * 10, "─" * 10, "─" * 10)

    t.add_row("[dim]toplam[/dim]", "", "", "")
    for label, key in [("Input", "input_tokens"), ("Output", "output_tokens"), ("Total", "total_tokens")]:
        t.add_row(label, _fmt(a[key]), _diff_str(a[key], b[key]), _fmt(b[key]))
    t.add_row("Cost $", f"${a['cost_usd']:.4f}", _diff_str(int(a['cost_usd'] * 10000), int(b['cost_usd'] * 10000)), f"${b['cost_usd']:.4f}")

    return Panel(t, title="[bold]Comparison[/bold]", border_style="white")


def _build_renderable(sessions: list[dict]) -> object:
    if len(sessions) == 2:
        a, b = sessions[0], sessions[1]
        cols = Columns([_make_session_panel(a, "cyan"), _make_session_panel(b, "yellow")], equal=True, expand=True)
        from rich.console import Group
        return Group(cols, _compare_panel(a, b))
    return _make_full_table(sessions)


def _apply_deltas(sessions: list[dict], prev: dict[str, dict]) -> None:
    """Attach delta fields to each session based on previous snapshot."""
    _KEYS = ("input_tokens", "output_tokens", "cache_write", "cache_read")
    for s in sessions:
        sid = s["session_id"]
        p = prev.get(sid)
        if p:
            s["delta_input"]   = s["input_tokens"] - p["input_tokens"]
            s["delta_output"]  = s["output_tokens"] - p["output_tokens"]
            s["delta_cache_w"] = s["cache_write"]   - p["cache_write"]
            s["delta_cache_r"] = s["cache_read"]    - p["cache_read"]
            s["delta_cost"] = round(
                s["delta_input"]   * _PRICE_INPUT +
                s["delta_output"]  * _PRICE_OUTPUT +
                s["delta_cache_w"] * _PRICE_CACHE_WRITE +
                s["delta_cache_r"] * _PRICE_CACHE_READ,
                5,
            )
        else:
            s["delta_input"] = s["delta_output"] = s["delta_cache_w"] = s["delta_cache_r"] = 0
            s["delta_cost"] = 0.0
        prev[sid] = {k: s[k] for k in _KEYS}


def run_live(sessions: list[dict], refresh: float = 2.0, hours: int = 24) -> None:
    """Live-refresh token dashboard. Press Ctrl+C to stop."""
    console = Console()
    prev: dict[str, dict] = {}

    with Live(console=console, refresh_per_second=1 / refresh, screen=False) as live:
        while True:
            updated = get_recent_sessions(hours=hours)
            _apply_deltas(updated, prev)
            live.update(_build_renderable(updated))
            time.sleep(refresh)
