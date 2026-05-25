# LinkedIn Post — Phase 0

---

When an AI agent is connected to GitHub, Slack, Notion, and Jira — it can do everything. But not every user operating the agent should be able to trigger all of those actions.

For example, a contractor should only see Jira. A read-only analyst should never delete a repo. An admin gets everything.

Therefore, I experimented to build a permission-aware filter in Python + Pydantic that models exactly this:

- Tools on each MCP server are tagged with a required permission level (read / write / admin)
- Users hold per-server grants
- The filter returns only what that user can call — servers with zero access are omitted entirely

Permission hierarchy is additive: admin ⊇ write ⊇ read.

During this experiment, 80% of the work was designing the data model. Once that was right, the filter function was quick. The time taking part is mostly the data contract, not the algorithm.

Codebase: [https://github.com/jainudi48/ai-engineering-journey/tree/main/phase-0-python-survival-kit](https://github.com/jainudi48/ai-engineering-journey/tree/main/phase-0-python-survival-kit)  
Blog Post: [https://jainudi48.github.io/ai-engineering/python/pydantic/mcp/2026/05/24/mcp-permission-filter.html](https://jainudi48.github.io/ai-engineering/python/pydantic/mcp/2026/05/24/mcp-permission-filter.html)

#Python #Pydantic #MCP #ModelContextProtocol #AIEngineering #LLM

---

