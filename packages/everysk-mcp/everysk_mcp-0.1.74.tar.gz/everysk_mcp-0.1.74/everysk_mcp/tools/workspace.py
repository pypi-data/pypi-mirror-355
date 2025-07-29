###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from typing import Optional

from everysk.api import Workspace
from everysk.api.utils import EveryskList
from mcp.server.fastmcp import FastMCP

from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_workspace_tools(mcp: FastMCP) -> None:
    """Register all workspace tools with the given MCP instance."""

    @mcp.tool(
        description="Returns a list of workspaces previously created. The workspaces are returned in sorted order, with the most recent workspace appearing first."
    )
    def workspace_list(
        query: Optional[str] = fields.query,
        page_size: Optional[int] = fields.page_size,
    ) -> EveryskList[Workspace]:
        result = Workspace.list(query=query, page_size=page_size)
        return result
