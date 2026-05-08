import pytest


@pytest.fixture(autouse=True)
def reset_storage():
    from tasks_mcp.storage import clear
    clear()
    yield
