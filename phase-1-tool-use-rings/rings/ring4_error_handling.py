"""
┌─────────────────────────────────────────────────────────────────────────────┐
│  RING 4 — Error Handling                                                    │
│                                                                             │
│  Tools fail. Networks time out. Repos are private. APIs rate-limit.        │
│  Claude handles is_error=True in tool_result gracefully — it adapts its    │
│  plan rather than crashing or hallucinating a success.                     │
│                                                                             │
│  Pattern demonstrated:                                                     │
│    1. Claude calls tool A (succeeds)                                       │
│    2. Claude calls tool B (returns is_error=True — repo not found)         │
│    3. Claude acknowledges the failure and uses tool C as a fallback        │
│    4. Final answer reflects partial success, not a crash                   │
│                                                                             │
│  Key API detail: tool_result with is_error=True is still a valid message. │
│  Claude receives the error text as context and reasons about next steps.   │
└─────────────────────────────────────────────────────────────────────────────┘
"""

import json
import anthropic
from tools import execute_tool, schemas_for

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 8
DEFAULT_REPO = "anthropics/anthropic-sdk-python"
FAKE_REPO_NAME = "this-repo-does-not-exist-xyz"


def run(verbose: bool = True, repo: str = DEFAULT_REPO) -> str:
    """
    Ask Claude to look up two repos — one public (succeeds), one private/missing
    (fails with a 404). Claude should gracefully handle the error and still deliver
    a useful partial answer.
    """
    client = anthropic.Anthropic()
    owner = repo.split("/")[0]
    fake_repo = f"{owner}/{FAKE_REPO_NAME}"

    tools = schemas_for(
        "get_github_repo",
        "get_github_issues",
        "execute_python",
    )

    messages = [
        {
            "role":    "user",
            "content": (
                "I want to compare two repos: "
                f"1) {repo} (public) "
                f"2) {fake_repo} (private/missing). "
                "Get stats for both, and also use execute_python to compute "
                "what percentage of the public repo's issues are labeled 'bug'. "
                "If any repo is inaccessible, note that and continue."
            )
        }
    ]

    if verbose:
        print("\n" + "═" * 60)
        print("RING 4 — Error Handling")
        print("═" * 60)
        print(f"User: {messages[0]['content']}\n")

    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if verbose:
            print(f"[Loop {iteration}] stop_reason={response.stop_reason!r} "
                  f"blocks={[b.type for b in response.content]}")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            answer = next(b.text for b in response.content if b.type == "text")
            if verbose:
                print(f"\n[Claude] Final answer:\n{answer}")
                print("─" * 60 + "\n")
            return answer

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if verbose:
                print(f"  → {block.name}({block.input})")

            # ── Inject a forced error for the non-existent repo ────────────────
            if (
                block.name == "get_github_repo"
                and block.input.get("repo") == FAKE_REPO_NAME
            ):
                result_json = json.dumps({
                    "error": "404 Not Found — repository does not exist or is private",
                    "status_code": 404
                })
                is_error = True
            else:
                result_json, is_error = execute_tool(block.name, block.input)

            if verbose:
                status = "✗ ERROR" if is_error else "✓ OK"
                preview = result_json[:120].replace("\n", " ")
                print(f"    ← {status}: {preview}…")

            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": block.id,
                "content":     result_json,
                "is_error":    is_error,
            })

        messages.append({"role": "user", "content": tool_results})

    return "[RING 4] Hit MAX_ITERATIONS."


if __name__ == "__main__":
    run()
