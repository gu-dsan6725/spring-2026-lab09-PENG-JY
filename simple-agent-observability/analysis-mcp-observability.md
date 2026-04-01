# MCP Observability Analysis

![MCP tools `resolve-library-id` and `get-library-docs` in a Braintrust trace](braintrust-mcp-tool.png)
*Screenshot showing MCP tool invocation in Braintrust trace*

I connected to the **Context7** MCP server over streamable HTTP (`https://mcp.context7.com/mcp`) and exposed its documentation tools through Strands' `MCPClient` alongside the existing DuckDuckGo tool. The trace above comes from a run where I asked about FastAPI async endpoints. The model first called `resolve-library-id` to map "FastAPI" to its Context7 identifier (`/fastapi/fastapi`), then issued `get-library-docs` with a focused documentation query, before generating the final `chat` response using the retrieved content.

In Braintrust, **MCP tool calls** appear as `execute_tool` spans nested under `execute_event_loop_cycle`, exactly like other tools, each with its own duration and ordering relative to `chat` spans. The key difference from **DuckDuckGo** is visible in the span inputs and outputs: DuckDuckGo spans take open-ended text queries and return ranked web search hits, while the Context7 spans take structured arguments (a library identifier and a documentation-focused question) and return curated, version-aware documentation snippets. This makes MCP tool calls more predictable and easier to trace — the inputs are deterministic library identifiers rather than free-form search strings, and the outputs are documentation text rather than mixed web results.
