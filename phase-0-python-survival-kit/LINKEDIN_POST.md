# LinkedIn Post — Phase 0

---

When an AI agent is connected to GitHub, Slack, Notion, and Jira — it can do everything. But not every user should be able to trigger all of those actions.

A contractor should only see Jira. A read-only analyst should never delete a repo. An admin gets everything.

Built a permission-aware filter in Python + Pydantic that models exactly this:

- Tools on each MCP server are tagged with a required permission level (read / write / admin)
- Users hold per-server grants
- The filter returns only what that user can call — servers with zero access are omitted entirely

Permission hierarchy is additive: admin ⊇ write ⊇ read.

80% of the work was the data model. Once that was right, the filter function was 10 lines. The hard part is always the data contract, not the algorithm.

25 tests passing. Code: [GitHub Repo URL]

👉 [LinkedIn Post URL]

#Python #Pydantic #MCP #ModelContextProtocol #AIEngineering #LLM

---
