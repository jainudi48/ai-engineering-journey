# AI Engineering Journey

A 90-day hands-on preparation roadmap for AI Engineering roles.

Each phase produces a **real deliverable** — working code with tests — committed here. Every commit comes with a blog post (see `_posts/`) and a LinkedIn post.

## Phases

| Phase | Days | Deliverable | Status |
|-------|------|-------------|--------|
| 0 — Python Survival Kit | 1–4 | MCP Permission Filter (Python + Pydantic) | ✅ Done |
| 1 — FastAPI + LLM Gateway | 5–12 | LLM Gateway: auth, rate-limit, streaming | ⬜ Next |
| 2 — Tool Use + MCP Router | 13–22 | Smart MCP Router with dynamic tool selection | ⬜ |
| 3 — RAG + Memory Systems | 23–34 | Knowledge Agent with Chroma / pgvector | ⬜ |
| 4 — LangGraph + Multi-Agent | 35–48 | Planner → Executor → Critic agent system | ⬜ |
| 5 — Model Serving | 49–56 | Llama 3 via Ollama + vLLM gateway | ⬜ |
| 6 — Evals + LLMOps | 57–66 | LangSmith traces + 20-case eval suite | ⬜ |
| 7 — Observability | 67–72 | Prometheus + Grafana + OpenTelemetry | ⬜ |
| 8 — Capstone | 73–90 | Mini AI API Platform (full stack) | ⬜ |

## Structure

```
ai-engineering-journey/
├── phase-0-python-survival-kit/
│   ├── mcp_permission_filter/   # Python package
│   │   ├── models.py            # Pydantic models
│   │   ├── filter.py            # Core filter function
│   │   └── demo.py              # Runnable demo
│   ├── tests/
│   │   └── test_mcp_filter.py   # 25 pytest tests
│   └── requirements.txt
├── _posts/                      # GitHub Pages blog posts
└── README.md
```

## Running Phase 0

```bash
cd phase-0-python-survival-kit
pip install -r requirements.txt

# Run the demo
PYTHONPATH=. python -m mcp_permission_filter.demo

# Run tests
PYTHONPATH=. pytest tests/ -v
```

## Blog

Published at [jainudi48.github.io/ai-engineering-journey](https://jainudi48.github.io/ai-engineering-journey)
