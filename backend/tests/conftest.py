"""Test config — isolate the DB to a temp file so tests never touch dev data, and provide a
clean DB per test session. Sets env BEFORE app modules import so config picks it up."""
import os
import tempfile

os.environ.setdefault("DB_PATH", os.path.join(tempfile.gettempdir(), "ada_test.db"))
os.environ.setdefault("PII_SALT", "test-salt")

# fresh db file each run
_p = os.environ["DB_PATH"]
if os.path.exists(_p):
    os.remove(_p)

import pytest  # noqa: E402

from app import db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    db.init_db()
    yield
