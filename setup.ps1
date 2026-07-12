# Token Slayer — Windows one-shot setup
# Usage (PowerShell):  .\setup.ps1
# Usage (CMD/anywhere): powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"

function Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "  [X]  $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  Token Slayer — Setup" -ForegroundColor Cyan
Write-Host "  =====================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Python check ─────────────────────────────────────────────────────────
try {
    $pyVer = python --version 2>&1
    Ok $pyVer
} catch {
    Fail "Python not found. Install Python 3.11+ from https://python.org and re-run."
}

# ── 2. Virtual environment ───────────────────────────────────────────────────
if (-not (Test-Path ".venv")) {
    Write-Host "  Creating .venv..." -ForegroundColor Gray
    python -m venv .venv
    Ok ".venv created"
} else {
    Ok ".venv already exists"
}

# ── 3. Activate ─────────────────────────────────────────────────────────────
& .\.venv\Scripts\Activate.ps1

# ── 4. Upgrade pip ──────────────────────────────────────────────────────────
Write-Host "  Upgrading pip..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet

# ── 5. Install all extras ────────────────────────────────────────────────────
Write-Host "  Installing dependencies (this may take a minute)..." -ForegroundColor Gray
pip install -e ".[dev,mcp]" --quiet
Ok "All dependencies installed"

# ── 6. .env setup ───────────────────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Ok ".env created from .env.example (no API keys needed — Token Slayer runs locally)"
} else {
    Ok ".env already exists"
}

# ── 7. Register MCP server (.mcp.json) ───────────────────────────────────────
# Prefer a global pipx install so the generated .mcp.json works from ANY
# project on this machine (and can be copied to other people's machines
# as long as they also run `pipx install`). Falls back to this repo's
# .venv path, which only works on this machine, in this exact location.
$tslayerCommand = $null
try {
    pipx --version | Out-Null
    Write-Host "  Installing tslayer globally via pipx (portable across projects)..." -ForegroundColor Gray
    pipx install ".[mcp]" --force --quiet
    $tslayerCommand = "tslayer"
    Ok "tslayer installed globally — .mcp.json will use the bare 'tslayer' command"
} catch {
    Warn "pipx not found — .mcp.json will point at this repo's .venv (only works on this machine/path)"
    Warn "For a portable setup: pip install pipx, then re-run this script"
    $tslayerExe = (Resolve-Path ".venv\Scripts\tslayer.exe").Path
    $tslayerCommand = $tslayerExe -replace '\\', '\\'
}

$mcpJson = @"
{
  "mcpServers": {
    "tslayer": {
      "command": "$tslayerCommand",
      "args": ["mcp"],
      "type": "stdio"
    }
  }
}
"@
$mcpJson | Out-File -FilePath ".mcp.json" -Encoding utf8 -NoNewline
Ok ".mcp.json created (Claude Code will auto-load this)"

# ── 8. Smoke test ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Verifying..." -ForegroundColor Gray
$help = tslayer --help 2>&1 | Select-Object -First 3
$help | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

Write-Host ""
Write-Host "  ✓ Token Slayer is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Cyan
Write-Host "    1. Activate venv:  .\.venv\Scripts\Activate.ps1"
Write-Host "    2. Try it:  tslayer score ."
Write-Host "    3. Open project in Claude Code — MCP tools load automatically"
Write-Host ""
