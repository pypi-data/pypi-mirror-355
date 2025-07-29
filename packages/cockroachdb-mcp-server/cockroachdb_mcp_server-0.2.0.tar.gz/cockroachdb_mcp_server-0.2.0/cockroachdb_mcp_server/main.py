import os
from fastapi import FastAPI
from cockroachdb_mcp_server.routes import contexts, health, debug
from cockroachdb_mcp_server import __version__

app = FastAPI(title="CockroachDB MCP Server", version=__version__)

app.include_router(health.router)
app.include_router(contexts.router, prefix="/contexts")

# Optional debug/demo endpoints
if os.getenv("MCP_DEMO_MODE") == "true":
    print("[debug] Mounting /debug routes")
    app.include_router(debug.router, prefix="/debug")

print(f"[debug] MCP_DEMO_MODE = {os.getenv('MCP_DEMO_MODE')}")

print("[debug] Registered paths:")
for route in app.routes:
    print(f" - {route.path}")


@app.get("/")
def root():
    return {"message": "MCP Server is running"}
