###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from typing import List, Optional, Union

from everysk.api import Datastore
from everysk.api.utils import EveryskList
from mcp.server.fastmcp import FastMCP

from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_datastore_tools(mcp: FastMCP) -> None:
    """Register all datastore tools with the given MCP instance."""

    @mcp.tool(
        description="Returns a list of datastores previously created. The datastores are returned in sorted order, with the most recent datastore appearing first."
    )
    def datastore_list(
        query: Optional[str] = fields.query,
        workspace: Optional[str] = fields.workspace,
        page_size: Optional[int] = fields.page_size,
    ) -> EveryskList[Datastore]:
        result = Datastore.list(query=query, workspace=workspace, page_size=page_size)
        return result

    @mcp.tool(
        description="Retrieves the details of an existing datastore by supplying the datastore's id."
    )
    def datastore_retrieve(
        id: str = fields.id_, workspace: Optional[str] = fields.workspace
    ) -> Datastore:
        result = Datastore.retrieve(id=id, workspace=workspace)
        return result

    @mcp.tool(
        description="Filters a list of datastores based on the provided criteria."
    )
    def datastore_filter(
        workspace: Optional[str] = fields.workspace,
        limit: Optional[int] = fields.limit,
        tags: Optional[List[str]] = fields.tags,
        start: Optional[str] = fields.start_date,
        end: Optional[str] = fields.end_date,
        link_uid: Optional[str] = fields.link_uid,
    ) -> EveryskList[Datastore]:
        result = Datastore.filter(
            workspace=workspace,
            limit=limit,
            tags=tags,
            start=start,
            end=end,
            link_uid=link_uid,
        )
        return result

    @mcp.tool(
        description="Creates a new datastore and then returns the created datastore."
    )
    def datastore_create(
        name: str = fields.name,
        description: Optional[str] = fields.description,
        tags: List[str] = fields.tags,
        date: Optional[str] = fields.date,
        data: List[List[Union[str, int, float, bool]]] = fields.data_datastore,
        with_data: Optional[bool] = fields.with_data,
        workspace: Optional[str] = fields.workspace,
    ) -> Datastore:
        result = Datastore.create(
            name=name,
            description=description,
            tags=tags,
            date=date,
            data=data,
            with_data=with_data,
            workspace=workspace,
        )

        return result
