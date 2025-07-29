# cockroachdb-mcp-server

[![PyPI](https://img.shields.io/pypi/v/cockroachdb-mcp-server)](https://pypi.org/project/cockroachdb-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/cockroachdb-mcp-server)](https://pypi.org/project/cockroachdb-mcp-server/)
[![License](https://img.shields.io/github/license/viragtripathi/cockroachdb-mcp-server)](https://github.com/viragtripathi/crdb-dump/blob/main/LICENSE)
[![CI](https://github.com/viragtripathi/cockroachdb-mcp-server/actions/workflows/python-ci.yml/badge.svg)](https://github.com/viragtripathi/cockroachdb-mcp-server/actions)

A Model Context Protocol (MCP) server implemented in Python using FastAPI and CockroachDB.

---

## 🧠 What This Is

`cockroachdb-mcp-server` is a production-grade, spec-aligned MCP server that:

- Implements the [Model Context Protocol](https://modelcontextprotocol.io/introduction)
- Uses **CockroachDB** as a resilient, SQL-compatible backend
- Exposes full **CRUD APIs** for managing model contexts
- Stores context definitions as **JSONB**, allowing arbitrary input/output schema
- Works seamlessly with the [`cockroachdb-mcp-client`](https://github.com/viragtripathi/cockroachdb-mcp-client) CLI

---

## ✅ Feature Highlights

- ✅ REST API for MCP context management (`/contexts`)
- ✅ Schema bootstrapping via CLI flag or env var
- ✅ CRDB URL auto-detection and dialect fix
- ✅ ASCII banner and version info
- ✅ Structured logging and configurable log level
- ✅ Ready for `/run`, `/deploy`, `/evaluate` extensions

---

## 🚀 Quickstart

### 📦 Install from PyPI

```bash
pip install cockroachdb-mcp-server
````

### 🏃 Run with schema init

```bash
cockroachdb-mcp-server serve --init-schema --log-level INFO
```

Or:

```bash
export MCP_AUTO_INIT_SCHEMA=true
cockroachdb-mcp-server serve
```

> Server runs at `http://localhost:8081` by default

---

## 🔧 CLI Usage

```bash
cockroachdb-mcp-server serve --init-schema
cockroachdb-mcp-server serve --port 8081 --host 127.0.0.1 --reload
cockroachdb-mcp-server --version
cockroachdb-mcp-server --banner
```

---

## 🔐 Configuring the Database

### ✅ Set the `CRDB_URL` environment variable

```bash
export CRDB_URL="postgresql://root@localhost:26257/defaultdb?sslmode=disable"
```

> Automatically rewritten to `cockroachdb://...` under the hood for compatibility.

Alternatively, set it directly:

```bash
export CRDB_URL="cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"
```

✅ Both formats are supported.

---

## 🧪 API Endpoints

| Method | Path             | Description       |
|--------|------------------|-------------------|
| POST   | `/contexts`      | Create a context  |
| GET    | `/contexts`      | List all contexts |
| GET    | `/contexts/{id}` | Get context by ID |
| PUT    | `/contexts/{id}` | Update context    |
| DELETE | `/contexts/{id}` | Delete context    |

📘 [View full API reference →](docs/api.md)

📘 [View hosted API Docs](https://viragtripathi.github.io/cockroachdb-mcp-server/)

---

## 🧱 Schema Auto-Bootstrap

Run this manually:

```bash
cockroachdb-mcp-server serve --init-schema
```

Or automatically with:

```bash
export MCP_AUTO_INIT_SCHEMA=true
```

The schema created is:

```sql
CREATE TABLE IF NOT EXISTS mcp_contexts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context_name STRING NOT NULL,
  context_version STRING NOT NULL,
  body JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);
```

---

## 🔗 Related Projects

* [cockroachdb-mcp-client](https://github.com/viragtripathi/cockroachdb-mcp-client): CLI tool to manage MCP contexts, simulate LLM runs, export, and batch simulate across providers.

---

## 🙌 Contributions

This project is designed for internal and community use.

PRs welcome to extend functionality (auth, deployment support, `/evaluate`, telemetry, etc.).
