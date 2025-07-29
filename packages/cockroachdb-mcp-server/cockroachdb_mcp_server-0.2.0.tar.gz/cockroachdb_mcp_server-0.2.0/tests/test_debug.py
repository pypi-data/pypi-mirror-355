import os

# ✅ Set this before importing `app`
os.environ["MCP_DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from cockroachdb_mcp_server.main import app

client = TestClient(app)

def test_debug_info():
    res = client.get("/debug/info")
    assert res.status_code == 200
    assert "version" in res.json()

def test_debug_tables():
    res = client.get("/debug/tables")
    assert res.status_code == 200
    assert "tables" in res.json()

def test_debug_sql_valid():
    res = client.post("/debug/sql", json={"query": "SELECT 1"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_debug_sql_invalid():
    res = client.post("/debug/sql", json={"query": "DROP TABLE mcp_contexts"})
    assert res.status_code == 200
    assert "error" in res.json()
