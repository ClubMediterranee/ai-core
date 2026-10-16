# Step 0 — Confirm the clubmed_api MCP is available (HARD GATE — fail fast)

Before anything else, probe the MCP with two cheap reads — `mcp__clubmed_api__list_routes` (limit 1) **and** `mcp__clubmed_api__search_openapi` (a one-word query, `top_k: 1`). The first proves the server answers; the second proves the semantic-search backend §8 actually depends on is alive. A server that lists routes but cannot search would silently degrade every §8 entry to 🟡/🔴.

- If the tool is **not available** (server not connected) or the call errors, **stop immediately**. Do not generate any spec — §8 cannot be resolved without it. Print an actionable message:

  ```
  ❌ The clubmed_api MCP server is not connected — the spec skill cannot resolve the §8 Data Contract without it.

  To connect it:
    claude mcp add --transport http clubmed_api <MCP_HTTP_URL> --header "x-api-key: <YOUR_API_KEY>"

  Then restart Claude Code (MCP servers load at startup) and run this skill again.
  A valid x-api-key AND the MCP endpoint URL from the ClubMed API team are required.
  ```

- If the call returns routes, the server is live — proceed.
