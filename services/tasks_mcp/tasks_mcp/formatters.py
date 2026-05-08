import json
from datetime import datetime
from zoneinfo import ZoneInfo

from tasks_mcp.config import CHAR_LIMIT


def format_json(items: list, total: int, offset: int, limit: int) -> str:
    response = {
        "total": total,
        "count": len(items),
        "offset": offset,
        "has_more": total > offset + len(items),
        "next_offset": offset + len(items) if total > offset + len(items) else None,
        "items": items,
    }
    return json.dumps(response, indent=2, default=str)


def format_markdown(
    items: list,
    total: int,
    offset: int,
    limit: int,
    timezone: str | None = None,
    title: str = "Results",
) -> str:
    lines = [f"# {title}", "", f"Found {total} items (showing {len(items)})", ""]
    for item in items:
        name = item.get("title") or item.get("name", "Untitled")
        lines.append(f"## {name} ({item.get('id', '?')})")
        for key, value in item.items():
            if key in ("id", "title", "name"):
                continue
            if isinstance(value, str) and (
                key.endswith("_at") or key.endswith("_time") or key == "due_date"
            ):
                value = _format_timestamp(value, timezone)
            lines.append(f"- **{key}**: {value}")
        lines.append("")
    return "\n".join(lines)


def _format_timestamp(ts: str, tz: str | None = None) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if tz:
            dt = dt.astimezone(ZoneInfo(tz))
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except (ValueError, TypeError):
        return str(ts)


def enforce_char_limit(text: str, limit: int = CHAR_LIMIT):
    if len(text) <= limit:
        return text, False
    return (
        text[:limit]
        + f'\n\n[Truncated at {limit} chars. Use limit/offset or add filters to narrow results.]',
        True,
    )
