"""
┌─────────────────────────────────────────────────────────────────────────────┐
│  RING 3 — Parallel Multi-Tool Run                                           │
│                                                                             │
│  When Claude sees multiple INDEPENDENT data needs in one prompt, it emits   │
│  multiple tool_use blocks in the SAME response — no waiting between them.   │
│                                                                             │
│  Flow:                                                                      │
│    user message                                                             │
│       → Claude thinks → emits [tool_use_A, tool_use_B, tool_use_C]         │
│       → we execute A, B, C concurrently (ThreadPoolExecutor)               │
│       → we send [tool_result_A, tool_result_B, tool_result_C] in one turn  │
│       → Claude synthesises all three → end_turn                            │
│                                                                             │
│  What to watch: len(tool_use_blocks) > 1 in the same response.            │
│  This is the inference engine deciding that fan-out is more efficient.     │
└─────────────────────────────────────────────────────────────────────────────┘
"""

import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from tools import execute_tool, schemas_for

MODEL = "claude-sonnet-4-6"
DEFAULT_REPO = "anthropics/anthropic-sdk-python"


def run(verbose: bool = True, repo: str = DEFAULT_REPO) -> str:
    """
    Ask a question whose answer requires three independent data sources.
    Claude should return multiple tool_use blocks in a single response.
    We execute them concurrently and return all results in one user turn.
    """
    client = anthropic.Anthropic()

    tools = schemas_for(
        "get_github_repo",
        "get_github_contributors",
        "web_search",
    )

    # Craft a prompt that clearly signals three independent lookups
    messages = [
        {
            "role":    "user",
            "content": (
                f"Give me a complete snapshot of {repo}. "
                "I need all three of these simultaneously: "
                "(1) the repo metadata (stars, language, open issues), "
                "(2) the top 5 contributors by commit count, "
                f"(3) search the web for any known issues or recent news about '{repo}'. "
                "Combine all three into a concise summary."
            )
        }
    ]

    if verbose:
        print("\n" + "═" * 60)
        print("RING 3 — Parallel Multi-Tool Run")
        print("═" * 60)
        print(f"User: {messages[0]['content']}\n")

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    if verbose:
        print(f"[Claude] stop_reason={response.stop_reason!r}")
        blocks = [b.type for b in response.content]
        print(f"[Claude] content blocks: {blocks}")
        tool_count = blocks.count("tool_use")
        print(f"[Claude] ✓ {tool_count} tool_use block(s) in ONE response\n")

    # ── Collect all tool_use blocks ───────────────────────────────────────────
    tool_uses = [b for b in response.content if b.type == "tool_use"]

    if not tool_uses:
        # Claude answered without tools — still valid, just return the text
        text = next((b.text for b in response.content if b.type == "text"), "")
        return text

    # ── Execute concurrently ──────────────────────────────────────────────────
    results: dict[str, tuple[str, bool]] = {}

    def _execute(block):
        return block.id, execute_tool(block.name, block.input)

    with ThreadPoolExecutor(max_workers=len(tool_uses)) as pool:
        futures = {pool.submit(_execute, b): b for b in tool_uses}
        for future in as_completed(futures):
            block_id, (result_json, is_error) = future.result()
            results[block_id] = (result_json, is_error)
            if verbose:
                tool_name = futures[future].name
                status = "ERROR" if is_error else "OK"
                print(f"  [{status}] {tool_name} → {result_json[:100].replace(chr(10),' ')}…")

    if verbose:
        print()

    # ── Return ALL results in a single user turn ──────────────────────────────
    messages += [
        {"role": "assistant", "content": response.content},
        {
            "role": "user",
            "content": [
                {
                    "type":        "tool_result",
                    "tool_use_id": tool_id,
                    "content":     result_json,
                    "is_error":    is_error,
                }
                for tool_id, (result_json, is_error) in results.items()
            ]
        }
    ]

    final = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    assert final.stop_reason == "end_turn"
    answer = next(b.text for b in final.content if b.type == "text")

    if verbose:
        print(f"[Claude] Final answer:\n{answer}")
        print("─" * 60 + "\n")

    return answer


if __name__ == "__main__":
    run()
