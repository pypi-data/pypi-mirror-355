import os
import logging

logger = logging.getLogger(__name__)


def resolve_crdb_url() -> str:
    url = os.getenv("CRDB_URL")
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "cockroachdb://", 1)
    if os.getenv("DEBUG") == "1":
        logger.debug("Using CRDB URL: %s", url)

    return url or "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"
