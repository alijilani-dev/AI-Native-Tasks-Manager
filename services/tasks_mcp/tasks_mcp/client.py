import httpx

API_BASE = "http://localhost:8000"


async def api_request(
    endpoint: str,
    method: str = "GET",
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method,
            f"{API_BASE}/{endpoint}",
            json=json_data,
            params=params,
        )
        response.raise_for_status()
        return response.json()
