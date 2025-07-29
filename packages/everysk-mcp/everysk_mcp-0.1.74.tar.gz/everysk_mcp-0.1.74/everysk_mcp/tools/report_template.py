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

from everysk.api import ReportTemplate
from everysk.api.utils import EveryskList
from mcp.server.fastmcp import FastMCP

from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_report_template_tools(mcp: FastMCP) -> None:
    """Register all report template tools with the given MCP instance."""

    @mcp.tool(
        description="Returns a list of report templates previously generated. The report templates are returned in sorted order, with the most recent report template appearing first."
    )
    def report_template_list(
        query: Optional[str] = fields.query,
        page_size: Optional[int] = fields.page_size,
        workspace: Optional[str] = fields.workspace,
    ) -> EveryskList[ReportTemplate]:
        result = ReportTemplate.list(
            query=query, page_size=page_size, workspace=workspace
        )
        return result

    @mcp.tool(
        description="Retrieves the details of an existing report template by supplying the report template's id."
    )
    def report_template_retrieve(
        id: str = fields.id_, workspace: Optional[str] = fields.workspace
    ) -> ReportTemplate:
        result = ReportTemplate.retrieve(id=id, workspace=workspace)
        return result
