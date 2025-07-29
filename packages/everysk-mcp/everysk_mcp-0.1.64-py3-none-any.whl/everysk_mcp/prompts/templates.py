###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from typing import List, Literal, Optional

from mcp.server.fastmcp.prompts import base

from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_prompts(mcp):
    """Register all prompt templates with the given MCP instance."""

    @mcp.prompt(
        name="Set Context",
        description="Sets the context for the assistant to use in the current session.",
    )
    def set_context(
        workspace: Optional[str] = fields.workspace,
    ) -> List[base.Message]:
        workspace = workspace or "main"

        return [
            base.AssistantMessage(
                f"I will be working on the workspace: `{workspace}`. I will use the workflows, report templates, reports, portfolios, datastores and files in this workspace to perform tasks and answer your questions."
            ),
            base.AssistantMessage(
                "This is a very workflow-centric assistant, so I will always try to use an existing workflow to complete tasks and to answer questions. To this end, my first action will always be to immediately list the workflows available in the workspace and keep this information ready to use."
            ),
            base.AssistantMessage(
                "Whenever possible, I will prefer to generate results on the screen. Only when asked I will produce HTML code for reports, tables and other deliverables."
            ),
            base.AssistantMessage(
                "Whenever possible, I will prefer to use symbols instead of sec_ids in the output to the user."
            ),
        ]

    @mcp.prompt(
        name="Set Pre-Trade Compliance",
        description="Sets the pre-trade compliance rules for the assistant to use in the current session.",
    )
    def set_pretrade_compliance(
        operation: Literal["buy", "sell"] = fields.operation,
        quantity: str = fields.quantity,
        security: str = fields.security_ticker,
    ) -> List[base.Message]:
        outflow = "outflow (ie, the sale of a security)"
        inflow = "inflow (ie, the purchase of a security)"

        return [
            base.AssistantMessage(
                f"I will now create a new portfolio, which will simulate a {operation} operation. Using single-entry bookkeeping, I will create this new portfolio simulating an {outflow if operation == 'sell' else inflow}."
            ),
            base.AssistantMessage(
                "After creating the new portfolio, I should check for the existence of a workflow with portfolio merging capabilities. I will use it to merge the new portfolio with the base portfolio. For efficiency, I should first retrieve the required parameter list for the workflow using the `workflow_prepare_run` tool."
            ),
            base.AssistantMessage(
                "Finally, I should check for the existence of a compliance workflow. I will use it to run the compliance metrics using the merged portfolio. For efficiency, I should first retrieve the required parameter list for the workflow using the `workflow_prepare_run` tool."
            ),
            base.AssistantMessage(
                "With everything set up, I will now proceed with the trade simulation."
            ),
            base.UserMessage(
                f"Operation: {operation}, security: {security}, quantity: {quantity}"
            ),
        ]
