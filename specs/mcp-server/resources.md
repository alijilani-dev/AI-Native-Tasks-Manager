# MCP Server: Resources Specification

## Decision

**No MCP resources in v1.** All operations are exposed as tools.

Resources will be considered in a future iteration if agents show frequent read-only lookup patterns on the same data (e.g. repeatedly calling `tasks_get_task` on the same task IDs).

## Rationale

- Everything a resource provides, a tool does better with full validation, error handling, and structured responses.
- Tools are simpler to implement, test, and maintain.
- Resources add implementation complexity (URI template parsing, `registerResource` + `registerResourceList`) for marginal benefit given our current scope.

## When to Revisit

Add resources when:
1. Agents are observed making repetitive read-only calls to the same endpoints.
2. Performance profiling shows tool overhead is a bottleneck for read-heavy access patterns.
3. A specific client benefit is identified (some MCP clients optimize resource caching).

## Future Candidates

- `tasks:///task/{task_id}` — direct task document lookup
- `tasks:///config/defaults` — static configuration (reminder timeouts, category lists)
