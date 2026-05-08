from mcp.types import ToolAnnotations

from tasks_mcp.config import CHAR_LIMIT
from tasks_mcp.errors import handle_api_error
from tasks_mcp.formatters import enforce_char_limit, format_json, format_markdown
from tasks_mcp.mcp_instance import mcp
from tasks_mcp.storage import list_items


@mcp.tool(
    name="tasks_review",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def tasks_review(
    user_id: str = "default",
    status: str | None = None,
    type: str | None = None,
    search_text: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    is_overdue: bool | None = None,
    priority: int | None = None,
    limit: int = 20,
    offset: int = 0,
    response_format: str = "json",
    timezone: str | None = None,
) -> str:
    '''Review work items with filters and pagination.

    Query tasks, appointments, and reminders by status, date range, search text,
    type, priority, or overdue flag. Returns paginated results.

    Args:
        user_id: User identifier for data scoping (default: "default")
        status: Filter by status ("pending", "completed", "cancelled", "skipped")
        type: Filter by type ("task", "appointment", "reminder")
        search_text: Search in title and description
        date_from: Start of date range (ISO 8601 UTC)
        date_to: End of date range (ISO 8601 UTC)
        is_overdue: Filter to overdue items only
        priority: Filter by priority level (1-5)
        limit: Results per page (1-100, default: 20)
        offset: Number of results to skip (default: 0)
        response_format: "json" (default) or "markdown"
        timezone: IANA timezone for markdown timestamps (e.g. "America/New_York")

    Returns:
        Paginated results in JSON or Markdown format.
    '''
    try:
        clamped_limit = min(max(limit, 1), 100)
        clamped_offset = max(offset, 0)

        data = list_items(
            user_id=user_id,
            status=status,
            item_type=type,
            search_text=search_text,
            date_from=date_from,
            date_to=date_to,
            is_overdue=is_overdue,
            priority=priority,
            limit=clamped_limit,
            offset=clamped_offset,
        )

        items = data.get("items", [])
        total = data.get("total", 0)

        if response_format == "markdown":
            text = format_markdown(
                items, total=total, offset=clamped_offset, limit=clamped_limit,
                timezone=timezone, title="Work Items",
            )
        else:
            text = format_json(items, total=total, offset=clamped_offset, limit=clamped_limit)

        text, _ = enforce_char_limit(text, CHAR_LIMIT)
        return text

    except Exception as e:
        return handle_api_error(e)
