# claude-context-analyzer

A CLI tool that analyzes Python projects and generates an optimized `CLAUDE.md` to reduce token usage when working with Claude Code.

## What It Does

- Parses all `.py` files using **tree-sitter** (imports, functions, classes, line counts)
- Builds a **dependency graph** to identify the most-imported (highest-impact) files
- Scans **git history** to find hot files that change frequently
- Detects **potential dead code** — defined but never imported elsewhere
- Estimates **token savings** from a proper `.claudeignore`
- Generates a ready-to-use **CLAUDE.md** with all findings

## Installation

```bash
git clone https://github.com/yourusername/claude-context-analyzer
cd claude-context-analyzer
python -m venv .venv
.venv/Scripts/pip install -e .   # Windows
# or
.venv/bin/pip install -e .       # macOS/Linux
```

## Usage

### Analyze a project

```bash
cca analyze ./my-project
cca analyze ./my-project --tokens      # show token budget estimate
cca analyze ./my-project --dead-code   # show potential dead code
```

### Generate CLAUDE.md

```bash
cca generate-config ./my-project
# writes my-project/CLAUDE.md
```

## Example Output

```
╭─────────────────────── Project Analysis — test-project ─────────────────────────╮
│ File                              Lines  Funcs  Classes  Imports  Imported by  Hot │
│ app/config.py                        14      0        1        2            5      │
│ app/db/queries.py                    22      4        0        1            3      │
│ app/models/product.py                18      2        1        1            3  ●   │
│ ...                                                                                │
╰────────────────────────────────────────────────────────────────────────────────────╯

Token Budget Estimate
  Full project (no ignore):    2,840 tokens
  With .claudeignore:          1,950 tokens
  Estimated savings:             31.3%
```

## Token Counting Note

Uses `cl100k_base` (GPT-4 tokenizer) as an approximation — Claude's real tokenizer is not public. Counts are typically within ±10%.

## Limitations

- Only analyzes Python (`.py`) files
- Dynamic imports (`importlib`, `__import__`) are not tracked
- Dead code detection uses text search — `__all__` and dynamic attribute access may produce false negatives

## License

MIT
