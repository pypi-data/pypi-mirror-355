from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from cockroachdb_mcp_server.db.db_connection import get_sqlalchemy_engine

router = APIRouter()


class SQLQuery(BaseModel):
    query: str


@router.get("/info")
def get_database_info():
    """
    Returns CockroachDB version and current database name.
    Safe for both self-hosted and Cockroach Cloud.
    """
    engine = get_sqlalchemy_engine()
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
        db = conn.execute(text("SELECT current_database();")).scalar()
        return {
            "database": db,
            "version": version,
        }


@router.post("/sql")
def run_raw_sql(payload: SQLQuery):
    """
    Run a read-only SQL SELECT query.
    """
    query = payload.query.strip()
    if not query.lower().startswith("select"):
        return {"error": "❌ Only SELECT queries are allowed in demo mode."}

    engine = get_sqlalchemy_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()
            return [dict(row._mapping) for row in result]
    except Exception as e:
        return {"error": f"💥 Query failed: {str(e)}"}


@router.get("/tables")
def list_tables():
    """
    Lists all user-defined tables in the current database.
    Excludes CockroachDB system/internal tables.
    """
    engine = get_sqlalchemy_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """
                )
            ).fetchall()
            return {"tables": [row[0] for row in result]}
    except Exception as e:
        return {"error": f"❌ Failed to list tables: {str(e)}"}
