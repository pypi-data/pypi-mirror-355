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

from everysk.api import File
from everysk.api.utils import EveryskList
from mcp.server.fastmcp import FastMCP

from everysk_mcp.fields import definitions as fields
from everysk_mcp.utils import from_base64_to_utf8, from_utf8_to_base64


###############################################################################
# Implementation
###############################################################################
def register_file_tools(mcp: FastMCP) -> None:
    """Register all file tools with the given MCP instance."""

    @mcp.tool(
        description="Returns a list of files previously uploaded. The files are returned in sorted order, with the most recent file appearing first."
    )
    def file_list(
        query: Optional[str] = fields.query,
        workspace: Optional[str] = fields.workspace,
        page_size: Optional[int] = fields.page_size,
    ) -> EveryskList[File]:
        result = File.list(query=query, workspace=workspace, page_size=page_size)
        return result

    @mcp.tool(
        description="Retrieves the details of an existing file by supplying the file's id."
    )
    def file_retrieve(
        id: str = fields.id_, workspace: Optional[str] = fields.workspace
    ) -> File:
        file = File.retrieve(id=id, workspace=workspace)
        file["data"] = from_base64_to_utf8(file["data"]) if file["data"] else None
        return file

    @mcp.tool(description="Creates and then returns the new file.")
    def file_create(
        name: str = fields.name,
        description: str = fields.description,
        tags: Optional[List[str]] = fields.tags,
        data: str = fields.data_file,
        with_data: Optional[bool] = fields.with_data,
        content_type: Optional[
            Literal[
                "image/svg+xml",
                "image/bmp",
                "image/jpeg",
                "image/png",
                "image/gif",
                "application/xml",
                "text/xml",
                "application/javascript",
                "application/json",
                "text/plain",
                "text/csv",
                "application/csv",
                "text/x-comma-separated-values",
                "text/comma-separated-values",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
                "application/pdf",
                "application/zip",
                "application/x-zip-compressed",
                "application/octet-stream",
            ]
        ] = fields.content_type,
        workspace: Optional[str] = fields.workspace,
    ) -> File:
        result = File.create(
            name=name,
            description=description,
            tags=tags,
            data=from_utf8_to_base64(data),
            with_data=with_data,
            content_type=content_type,
            workspace=workspace,
        )
        return result
