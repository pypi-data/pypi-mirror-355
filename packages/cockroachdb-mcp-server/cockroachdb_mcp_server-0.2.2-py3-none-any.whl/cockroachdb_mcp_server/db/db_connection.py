from sqlalchemy import create_engine
from cockroachdb_mcp_server.config import resolve_crdb_url
import logging

logger = logging.getLogger(__name__)


def get_sqlalchemy_engine(opts=None):
    if opts is None:
        dsn = resolve_crdb_url()
        return create_engine(dsn)

    base = f"cockroachdb://root@{opts.get('host', 'localhost')}:{opts.get('port', 26257)}/{opts['db']}"
    if opts.get("certs_dir"):
        base += (
            f"?sslmode=verify-full"
            f"&sslrootcert={opts['certs_dir']}/ca.crt"
            f"&sslcert={opts['certs_dir']}/client.root.crt"
            f"&sslkey={opts['certs_dir']}/client.root.key"
        )
    else:
        base += "?sslmode=disable"

    logger.debug("Constructed CRDB DSN from opts: %s", base)
    return create_engine(base)
