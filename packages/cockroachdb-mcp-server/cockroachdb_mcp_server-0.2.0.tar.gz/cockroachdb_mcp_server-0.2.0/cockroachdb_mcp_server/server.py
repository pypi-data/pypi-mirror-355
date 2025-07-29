import uvicorn


def start_server(host="0.0.0.0", port=8081, reload=False, demo_mode=False):
    uvicorn.run("cockroachdb_mcp_server.main:app", host=host, port=port, reload=reload)
