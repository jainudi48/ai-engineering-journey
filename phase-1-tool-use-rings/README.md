# Phase 1 — Tool Use Rings

**GitHub Repo Health Checker** — a self-contained demo of five tool-use patterns in the Anthropic Python SDK.

Runs health checks against any public GitHub repo using real GitHub REST API calls (no auth needed). Defaults to `anthropics/anthropic-sdk-python`.

---

## The 5 Rings

| Ring | Pattern | Key concept |
|------|---------|-------------|
| 1 | Single Tool, Single Run | `stop_reason="tool_use"` → execute → `tool_result` → `end_turn` |
| 2 | Agentic Loop | Loop until `end_turn`; Claude decides order and count |
| 3 | Parallel Multi-Tool Run | Multiple `tool_use` blocks in one response; execute concurrently |
| 4 | Error Handling | `is_error=True` in `tool_result`; Claude adapts gracefully |
| 5 | Beta SDK + ToolRunner | `client.beta.messages.create()` + abstraction class |

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python demo.py                              # all 5 rings, default repo
python demo.py --repo torvalds/linux        # target a different public repo
python demo.py --ring 3                     # parallel tools only
python demo.py --ring 3 --repo pallets/flask  # specific ring + custom repo
python demo.py --quiet                      # final answers only, no step logs
```

The `--repo` flag accepts any public GitHub repo in `OWNER/REPO` format and defaults to `anthropics/anthropic-sdk-python`.

## Tests

```bash
pytest tests/ -v           # 18 unit tests, no API key needed
```

## Structure

```
phase-1-tool-use-rings/
├── tools/
│   ├── __init__.py          # unified dispatcher + schemas_for()
│   ├── github_tools.py      # get_github_repo, issues, PRs, contributors
│   ├── code_executor.py     # execute_python (subprocess, 10s timeout)
│   └── web_search_tool.py   # web_search (DuckDuckGo instant answer)
├── rings/
│   ├── ring1_single_tool.py
│   ├── ring2_agentic_loop.py
│   ├── ring3_parallel_tools.py
│   ├── ring4_error_handling.py
│   └── ring5_beta_sdk.py    # ToolRunner class + beta flag
├── tests/
│   └── test_rings.py        # 18 unit tests (mocked network)
├── demo.py
└── LINKEDIN_POST.md
```

---

*Part of [ai-engineering-journey](https://github.com/jainudi48/ai-engineering-journey) — a 90-day AI Engineering roadmap.*
