"""
┌─────────────────────────────────────────────────────────────────────────────┐
│  RING 5 — Beta SDK ToolRunner Abstraction                                   │
│                                                                             │
│  Two ideas combined:                                                        │
│                                                                             │
│  A) anthropic.beta.messages.create()                                       │
│     The Python SDK exposes beta features via client.beta.messages.         │
│     We use betas=["token-efficient-tools-2025-02-19"] which sends tool     │
│     schemas in a more compact format, reducing prompt tokens by ~40%       │
│     when you have many tools. Same behaviour, less cost.                   │
│                                                                             │
│  B) ToolRunner class                                                        │
│     Encapsulates the entire agentic loop (Ring 2 pattern) behind a clean   │
│     interface: runner.run(prompt) → answer. Callers never see messages[],  │
│     stop_reason checks, or tool_result construction.                       │
│                                                                             │
│  Together these represent production-grade tool use: the SDK handles beta  │
│  optimisations, the ToolRunner handles orchestration complexity.           │
│                                                                             │
│  What to watch: the betas= parameter in create(), and how ToolRunner       │
│  makes adding new tools a one-liner instead of a copy-paste problem.       │
└─────────────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import anthropic
from typing import Callable
from tools import execute_tool, schemas_for, ALL_SCHEMAS

MODEL      = "claude-sonnet-4-6"
BETA_FLAG  = "token-efficient-tools-2025-02-19"
MAX_ITERS  = 10


# ══════════════════════════════════════════════════════════════════════════════
#  ToolRunner — the abstraction
# ══════════════════════════════════════════════════════════════════════════════

class ToolRunner:
    """
    A self-contained agentic loop that uses the Anthropic beta SDK.

    Usage:
        runner = ToolRunner(tool_names=["get_github_repo", "web_search"])
        answer = runner.run("Summarise the anthropics/anthropic-sdk-python repo.")

    Internally it:
      - Calls client.beta.messages.create() with the token-efficient-tools beta
      - Loops until stop_reason == "end_turn"
      - Dispatches every tool_use block through the unified execute_tool()
      - Optionally streams verbose logs via an on_event callback
    """

    def __init__(
        self,
        tool_names: list[str] | None = None,
        model: str = MODEL,
        max_tokens: int = 1024,
        max_iterations: int = MAX_ITERS,
        on_event: Callable[[str], None] | None = None,
    ):
        self._client        = None   # lazy-initialised on first run() call
        self.tools          = schemas_for(*(tool_names or list(ALL_SCHEMAS)))
        self.model          = model
        self.max_tokens     = max_tokens
        self.max_iterations = max_iterations
        self._log           = on_event or (lambda _: None)

    # ── Lazy client (avoids requiring ANTHROPIC_API_KEY at import time) ───────

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, prompt: str) -> str:
        """Run the agentic loop for a single prompt. Returns final text."""
        messages = [{"role": "user", "content": prompt}]
        self._log(f"[ToolRunner] Prompt: {prompt[:80]}…")

        for i in range(1, self.max_iterations + 1):
            self._log(f"[ToolRunner] Iteration {i}")

            # ── Beta SDK call ─────────────────────────────────────────────────
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=self.tools,
                messages=messages,
                betas=[BETA_FLAG],           # ← the beta magic
            )

            self._log(f"[ToolRunner]   stop_reason={response.stop_reason!r} "
                      f"blocks={[b.type for b in response.content]}")

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                return next(
                    b.text for b in response.content if b.type == "text"
                )

            # ── Execute tools ─────────────────────────────────────────────────
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                self._log(f"[ToolRunner]   → {block.name}({block.input})")
                result_json, is_error = execute_tool(block.name, block.input)
                self._log(f"[ToolRunner]     ← {'ERR' if is_error else 'OK'}")
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result_json,
                    "is_error":    is_error,
                })
            messages.append({"role": "user", "content": tool_results})

        return "[ToolRunner] Reached max_iterations without end_turn."

    # ── Convenience class methods ─────────────────────────────────────────────

    @classmethod
    def for_github(cls, **kwargs) -> "ToolRunner":
        """Pre-configured runner for GitHub analysis tasks."""
        return cls(
            tool_names=["get_github_repo", "get_github_issues", "get_github_prs"],
            **kwargs
        )

    @classmethod
    def for_research(cls, **kwargs) -> "ToolRunner":
        """Pre-configured runner for research tasks (GitHub + web + code exec)."""
        return cls(
            tool_names=["get_github_repo", "web_search", "execute_python"],
            **kwargs
        )


# ══════════════════════════════════════════════════════════════════════════════
#  Demo
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_REPO = "anthropics/anthropic-sdk-python"


def run(verbose: bool = True, repo: str = DEFAULT_REPO) -> str:
    """
    Full repo health analysis using ToolRunner + beta SDK.
    Identical outcome to Ring 2, but zero boilerplate at the call site.
    """
    if verbose:
        print("\n" + "═" * 60)
        print("RING 5 — Beta SDK ToolRunner Abstraction")
        print("═" * 60)
        print(f"  Beta flag: {BETA_FLAG}")
        print(f"  Abstraction: ToolRunner.for_research()\n")

    def _log(msg: str):
        if verbose:
            print(msg)

    runner = ToolRunner.for_research(on_event=_log)

    answer = runner.run(
        f"Give me a comprehensive health report on {repo}. "
        "Include: repo stats, any critical open issues, and search the web for the "
        f"latest release version of '{repo}'. Then use execute_python to compute the ratio of "
        "stars to forks (use the numbers you found). "
        "Format as a concise markdown report."
    )

    if verbose:
        print(f"\n[ToolRunner] Final answer:\n{answer}")
        print("─" * 60 + "\n")

    return answer


if __name__ == "__main__":
    run()
