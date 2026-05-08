from tasks_mcp.config import (
    CHAR_LIMIT,
    LIMIT_DEFAULT,
    LIMIT_MAX,
    LIMIT_MIN,
    PORT,
    USER_ID_DEFAULT,
)


def test_port():
    assert PORT == 8000


def test_limit_default():
    assert LIMIT_DEFAULT == 20


def test_limit_max():
    assert LIMIT_MAX == 100


def test_limit_min():
    assert LIMIT_MIN == 1


def test_char_limit():
    assert CHAR_LIMIT == 25000


def test_user_id_default():
    assert USER_ID_DEFAULT == "default"
