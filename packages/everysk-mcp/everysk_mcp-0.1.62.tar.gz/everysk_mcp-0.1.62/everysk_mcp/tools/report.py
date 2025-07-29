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

from everysk.api import Report
from everysk.api.utils import EveryskList
from mcp.server.fastmcp import FastMCP

from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_report_tools(mcp: FastMCP) -> None:
    """Register all report tools with the given MCP instance."""

    @mcp.tool(
        description="Returns a list of reports previously generated. The reports are returned in sorted order, with the most recent report appearing first."
    )
    def report_list(
        query: Optional[str] = fields.query,
        workspace: Optional[str] = fields.workspace,
        page_size: Optional[int] = fields.page_size,
    ) -> EveryskList[Report]:
        result = Report.list(query=query, workspace=workspace, page_size=page_size)
        return result

    @mcp.tool(
        description="Retrieves the details of an existing report by supplying the report's id."
    )
    def report_retrieve(
        id: str = fields.id_, workspace: Optional[str] = fields.workspace
    ) -> Report:
        result = Report.retrieve(id=id, workspace=workspace)
        return result
