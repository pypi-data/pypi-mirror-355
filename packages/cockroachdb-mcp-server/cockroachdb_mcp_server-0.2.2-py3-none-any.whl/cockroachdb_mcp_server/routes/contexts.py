from fastapi import APIRouter, HTTPException
from cockroachdb_mcp_server.models.context import ContextRequest
from sqlalchemy import text
from cockroachdb_mcp_server.db.db_connection import get_sqlalchemy_engine
from uuid import UUID
import json

engine = get_sqlalchemy_engine()

router = APIRouter()


@router.post("")
def create_context(request: ContextRequest):
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO mcp_contexts (context_name, context_version, body)
                    VALUES (:name, :version, :body)
                """
                ),
                {
                    "name": request.name,
                    "version": request.version,
                    "body": json.dumps(request.body),
                },
            )
        return {"status": "created", "context_name": request.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def list_contexts():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, context_name, context_version, created_at FROM mcp_contexts"
                )
            )
            rows = [dict(row._mapping) for row in result.fetchall()]
        return {"contexts": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{context_id}")
def get_context(context_id: UUID):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT id, context_name, context_version, body, created_at FROM mcp_contexts WHERE id = :id"
            ),
            {"id": str(context_id)},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Context not found")
        return dict(row._mapping)


@router.put("/{context_id}")
def update_context(context_id: UUID, request: ContextRequest):
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE mcp_contexts
                    SET context_name = :name,
                        context_version = :version,
                        body = :body
                    WHERE id = :id
                """
                ),
                {
                    "id": str(context_id),
                    "name": request.name,
                    "version": request.version,
                    "body": json.dumps(request.body),
                },
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Context not found")
        return {"status": "updated", "context_id": str(context_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{context_id}")
def delete_context(context_id: UUID):
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM mcp_contexts WHERE id = :id"), {"id": str(context_id)}
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Context not found")
        return {"status": "deleted", "context_id": str(context_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
