"""
┌─────────────────────────────────────────────────────────────────────────────┐
│  RING 2 — Agentic Loop                                                      │
│                                                                             │
│  The core pattern behind every AI agent. We keep calling messages.create() │
│  until stop_reason == "end_turn". Each iteration:                          │
│    1. Claude decides whether to call a tool or answer                      │
│    2. If tool_use → we execute, append tool_result, loop                   │
│    3. If end_turn  → we return the final answer                            │
│                                                                             │
│  Claude chooses WHICH tools to call and IN WHAT ORDER — we never hard-code │
│  the sequence. This is the key difference from Ring 1.                     │
│                                                                             │
│  What to watch: the message list grows on each iteration, forming a        │
│  conversation history that gives Claude its memory of what it already did. │
└─────────────────────────────────────────────────────────────────────────────┘
"""

import anthropic
from tools import execute_tool, schemas_for

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10   # safety cap — prevents infinite loops in production
DEFAULT_REPO = "anthropics/anthropic-sdk-python"


def run(verbose: bool = True, repo: str = DEFAULT_REPO) -> str:
    """
    Give Claude a compound question that requires multiple tool calls.
    The agentic loop runs until Claude is satisfied with its answer.
    Returns the final text response.
    """
    client = anthropic.Anthropic()

    tools = schemas_for(
        "get_github_repo",
        "get_github_issues",
        "get_github_prs",
    )

    messages = [
        {
            "role":    "user",
            "content": (
                f"Assess the health of the {repo} repository. "
                "I want to know: (1) basic repo stats, (2) the 3 most recent open issues "
                "with their labels, and (3) whether there are open PRs. "
                "Summarise your findings in 3 bullet points."
            )
        }
    ]

    if verbose:
        print("\n" + "═" * 60)
        print("RING 2 — Agentic Loop")
        print("═" * 60)
        print(f"User: {messages[0]['content']}\n")

    iteration = 0

    # ── THE LOOP ──────────────────────────────────────────────────────────────
    while iteration < MAX_ITERATIONS:
        iteration += 1

        if verbose:
            print(f"[Loop iteration {iteration}]")

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if verbose:
            print(f"  stop_reason={response.stop_reason!r}")
            print(f"  blocks: {[b.type for b in response.content]}")

        # Append Claude's response to the conversation
        messages.append({"role": "assistant", "content": response.content})

        # ── End condition ──────────────────────────────────────────────────────
        if response.stop_reason == "end_turn":
            answer = next(b.text for b in response.content if b.type == "text")
            if verbose:
                print(f"\n[Claude] Final answer (after {iteration} iterations):\n{answer}")
                print("─" * 60 + "\n")
            return answer

        # ── Execute all tool calls in this response ────────────────────────────
        # Claude may request multiple tools in one response (Ring 3 will show this
        # intentionally; here it happens incidentally).
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if verbose:
                print(f"  → Tool call: {block.name}({block.input})")

            result_json, is_error = execute_tool(block.name, block.input)

            if verbose:
                preview = result_json[:150].replace("\n", " ")
                print(f"    ← {'ERROR' if is_error else 'OK'}: {preview}…")

            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": block.id,
                "content":     result_json,
                "is_error":    is_error,
            })

        # Append all tool results in a single user turn
        messages.append({"role": "user", "content": tool_results})

    return "[RING 2] Hit MAX_ITERATIONS without end_turn — increase the cap or narrow the query."


if __name__ == "__main__":
    run()
