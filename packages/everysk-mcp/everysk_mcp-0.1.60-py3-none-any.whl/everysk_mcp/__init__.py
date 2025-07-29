###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
__all__ = ["main", "server"]
from everysk.core.log import Logger

from . import server


def main() -> None:
    # Initialize the logger
    logger = Logger(__name__)

    # Start the MCP server
    logger.info("Everysk MCP server running...")

    server.mcp.run(transport="stdio")
