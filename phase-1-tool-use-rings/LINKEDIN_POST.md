# LinkedIn Post — Phase 1: Tool Use Rings

---

Claude called 3 tools in parallel. I never told it to.

I built a GitHub Repo Health Checker using the Anthropic Python SDK. Point it at any public repo and it runs a full health check. Along the way I implemented 5 tool-use patterns, each one teaching something different about how tool use actually works under the hood.

The thing that clicked for me: the model does not call tools. It generates structured JSON describing what it wants called, then waits. Your code runs the tool and sends the result back. Claude resumes and either calls another tool or gives the final answer. That loop is the entire foundation of agentic AI.

The 5 patterns I implemented:

Ring 1: One tool, one call, done. The base pattern everything else builds on.

Ring 2: Agentic loop. Keep looping until Claude says it is done. It calls repo stats, issues, and PRs in whatever order it decides. You never hardcode the sequence.

Ring 3: Parallel tool calls. Ask for everything at once and Claude returns multiple tool calls in a single response. Execute them concurrently. The model decides the fan-out.

Ring 4: Error handling. When a repo returns 404, Claude does not crash. It reasons about the failure and gives a partial answer. is_error=True is a first class design concept, not a hack.

Ring 5: ToolRunner abstraction. Wrap the whole loop in a class. The call site becomes one line. The beta SDK flag also cuts token usage by around 40% with many tools.

One thing worth knowing: the tool description is the decision logic. There is no separate planner. Claude reads your schema and decides when to call what based on how you describe the tool. Vague descriptions produce unpredictable agents. Precise ones produce reliable ones.

Blog: jainudi48.github.io/ai-engineering-journey
Code: github.com/jainudi48/ai-engineering-journey/tree/main/phase-1-tool-use-rings

#AIEngineering #Anthropic #Claude #ToolUse #AgenticAI #Python #LLM #BuildInPublic

---

*Character count guidance: ~1,450 characters*
