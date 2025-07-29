###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from typing import List, Dict

from mcp.server.fastmcp import FastMCP


###############################################################################
# Implementation
###############################################################################
def register_static_resources(mcp: FastMCP) -> None:
    """ Register all static resources with the given MCP instance. """

    @mcp.resource(
        uri='config://color-palette', 
        name='Get color palette', 
        description='Returns the color palette used in the application.'
    )
    def get_color_palette() -> Dict[str, List[str]]:
        return {
            'primary': ['#FFFFFF', '#121212', '#FF832A'],
            'secondary': ['#FFB884', '#232323'],
            'tertiary': ['#F4F4F4', '#7B7B7B'],
        }

