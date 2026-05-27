"""
┌─────────────────────────────────────────────────────────────────────────────┐
│  RING 1 — Single Tool, Single Run                                           │
│                                                                             │
│  The foundational pattern. One tool declared, one tool_use block returned,  │
│  one tool_result sent back, conversation ends.                              │
│                                                                             │
│  Flow:                                                                      │
│    user message                                                             │
│       → Claude thinks → emits tool_use (stop_reason="tool_use")            │
│       → we execute the tool                                                 │
│       → we send tool_result                                                 │
│       → Claude produces final answer (stop_reason="end_turn")              │
│                                                                             │
│  What to watch: the stop_reason flip and the tool_use/tool_result pairing  │
└─────────────────────────────────────────────────────────────────────────────┘
"""

import anthropic
from tools import execute_tool, schemas_for

MODEL = "claude-sonnet-4-6"
DEFAULT_REPO = "anthropics/anthropic-sdk-python"


def run(verbose: bool = True, repo: str = DEFAULT_REPO) -> str:
    """
    Ask Claude one question that requires one GitHub tool call.
    Returns Claude's final text response.
    """
    client = anthropic.Anthropic()

    # ── Step 1: Send user message with one tool available ─────────────────────
    messages = [
        {
            "role":    "user",
            "content": (
                f"What is the star count, primary language, and description "
                f"of the GitHub repo {repo}?"
            )
        }
    ]

    if verbose:
        print("\n" + "═" * 60)
        print("RING 1 — Single Tool, Single Run")
        print("═" * 60)
        print(f"User: {messages[0]['content']}\n")

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=schemas_for("get_github_repo"),   # only one tool available
        messages=messages,
    )

    if verbose:
        print(f"[Claude] stop_reason={response.stop_reason!r}")
        print(f"[Claude] content blocks: {[b.type for b in response.content]}\n")

    # ── Step 2: Claude emits tool_use — we execute it ─────────────────────────
    assert response.stop_reason == "tool_use", (
        f"Expected 'tool_use', got {response.stop_reason!r}"
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")

    if verbose:
        print(f"[Tool call] {tool_block.name}({tool_block.input})")

    result_json, is_error = execute_tool(tool_block.name, tool_block.input)

    if verbose:
        print(f"[Tool result] is_error={is_error}")
        print(result_json[:300], "...\n" if len(result_json) > 300 else "\n")

    # ── Step 3: Return tool_result to Claude ──────────────────────────────────
    messages += [
        {"role": "assistant", "content": response.content},
        {
            "role": "user",
            "content": [
                {
                    "type":        "tool_result",
                    "tool_use_id": tool_block.id,
                    "content":     result_json,
                    "is_error":    is_error,
                }
            ]
        }
    ]

    final = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=schemas_for("get_github_repo"),
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
