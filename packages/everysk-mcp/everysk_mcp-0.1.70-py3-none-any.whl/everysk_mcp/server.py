###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from mcp.server.fastmcp import FastMCP

from everysk_mcp.prompts.templates import register_prompts
from everysk_mcp.resources.static import register_static_resources
from everysk_mcp.resources.templates import register_template_resources
from everysk_mcp.tools.calculation import register_calculation_tools
from everysk_mcp.tools.datastore import register_datastore_tools
from everysk_mcp.tools.file import register_file_tools
from everysk_mcp.tools.portfolio import register_portfolio_tools
from everysk_mcp.tools.report import register_report_tools
from everysk_mcp.tools.report_template import register_report_template_tools
from everysk_mcp.tools.workflow import register_workflow_tools
from everysk_mcp.tools.workflow_execution import register_workflow_execution_tools
from everysk_mcp.tools.workspace import register_workspace_tools

###############################################################################
# Implementation
###############################################################################

mcp = FastMCP(
    "Everysk MCP Server",
    instructions="This is a very workflow-centric assistant, so always try to use an existing workflow to complete tasks and to answer questions. To this end, the first action will always be to immediately list the workflows available in the workspace and keep this information ready to use. Whenever possible, results will be rendered on the screen. Only when asked code will be generated for reports, tables and other deliverables. Whenever possible, symbols will be used in the output to the user instead of sec_ids.",
    version="0.1.70",
)

# Register all prompts
register_prompts(mcp)

# Register all resources
register_static_resources(mcp)
register_template_resources(mcp)

# Register all tools
register_calculation_tools(mcp)
register_datastore_tools(mcp)
register_file_tools(mcp)
register_portfolio_tools(mcp)
register_report_template_tools(mcp)
register_report_tools(mcp)
register_workflow_execution_tools(mcp)
register_workflow_tools(mcp)
register_workspace_tools(mcp)
