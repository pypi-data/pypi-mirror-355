from sqlalchemy import create_engine, text
from sqlalchemy_cockroachdb import run_transaction
from cockroachdb_mcp_server.config import resolve_crdb_url


def run_schema_init(dsn):
    dsn = resolve_crdb_url()
    assert dsn.startswith("cockroachdb://"), f"Expected cockroachdb://, got {dsn}"
    engine = create_engine(dsn)

    def callback(conn):
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS mcp_contexts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                context_name STRING NOT NULL,
                context_version STRING NOT NULL,
                body JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT now()
            )
        """
            )
        )

    run_transaction(engine, callback)
