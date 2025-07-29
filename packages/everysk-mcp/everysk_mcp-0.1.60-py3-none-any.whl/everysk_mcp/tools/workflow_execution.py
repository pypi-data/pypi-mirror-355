###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from everysk.api import WorkflowExecution
from mcp.server.fastmcp import FastMCP

from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_workflow_execution_tools(mcp: FastMCP) -> None:
    """Register all workflow execution tools with the given MCP instance."""

    @mcp.tool(
        description="Retrieves the details of an existing workflow execution by supplying the execution's id."
    )
    def workflow_execution_retrieve(
        workflow_id: str = fields.id_, workflow_execution_id: str = fields.id_
    ) -> WorkflowExecution:
        execution = WorkflowExecution.retrieve(
            workflow_id=workflow_id, workflow_execution_id=workflow_execution_id
        )
        return execution
