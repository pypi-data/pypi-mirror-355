###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from typing import Any, Dict, Optional

from everysk.api import Workflow, WorkflowExecution
from everysk.api.utils import EveryskList
from mcp.server.fastmcp import FastMCP

from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_workflow_tools(mcp: FastMCP) -> None:
    """Register all workflow tools with the given MCP instance."""

    @mcp.tool(
        description="Returns a list of workflows you've previously created. The workflows are returned in sorted order, with the most recent workflow appearing first."
    )
    def workflow_list(
        query: Optional[str] = fields.query,
        workspace: Optional[str] = fields.workspace,
        page_size: Optional[int] = fields.page_size,
    ) -> EveryskList[Workflow]:
        result = Workflow.list(query=query, workspace=workspace, page_size=page_size)
        return result

    @mcp.tool(
        description="Retrieves the details of an existing workflow by supplying the workflow's id."
    )
    def workflow_retrieve(
        id: str = fields.id_, workspace: Optional[str] = fields.workspace
    ) -> Workflow:
        result = Workflow.retrieve(id=id, workspace=workspace)
        return result

    @mcp.tool(
        description="Provides information about the required parameters to run a workflow and details on its output. It should always be called before running a workflow using the `workflow_run` tool. This tool retrieves the workflow details and prepares the context for running it, so I should not use `workflow_retrieve` if I am going to use this tool."
    )
    def workflow_prepare_run(
        id: str = fields.id_,
        workspace: Optional[str] = fields.workspace,
    ) -> str:
        wf = workflow_retrieve(id=id, workspace=workspace)

        for worker in wf.workers:
            if worker["id"] == wf.starter_worker_id:
                starter_context = str(worker["script_outputs"])
            elif worker["id"] == wf.ender_worker_id:
                ender_context = str(worker["script_outputs"])

        return (
            f"The workflow `{wf.name}` accepts the following parameters:\n\n"
            f"{starter_context}"
            f"The workflow `{wf.name}` will return the following outputs:\n\n"
            f"{ender_context}"
            f"You can now run the workflow using the `workflow_run` tool with the required parameters."
        )

    @mcp.tool(
        description="Runs a specific workflow through the api. It should be called after the `workflow_prepare_run` tool to ensure that the workflow is ready to be executed with the provided parameters."
    )
    def workflow_run(
        id: str = fields.id_,
        workspace: Optional[str] = fields.workspace,
        parameters: Dict[str, Any] = fields.parameters,
        synchronous: Optional[bool] = fields.synchronous,
    ) -> WorkflowExecution:
        execution = Workflow.run(
            id=id, workspace=workspace, parameters=parameters, synchronous=synchronous
        )
        return execution
