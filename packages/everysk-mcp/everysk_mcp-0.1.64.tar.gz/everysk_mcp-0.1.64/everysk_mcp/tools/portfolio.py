###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from typing import List, Optional

from everysk.api import Portfolio
from everysk.api.utils import EveryskList
from mcp.server.fastmcp import FastMCP

from everysk_mcp.blueprints.securities import Security
from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def register_portfolio_tools(mcp: FastMCP) -> None:
    """Register all portfolio tools with the given MCP instance."""

    @mcp.tool(
        description="Returns a list of portfolios previously created. The portfolios are returned in sorted order, with the most recent portfolio appearing first."
    )
    def portfolio_list(
        query: Optional[str] = fields.query,
        workspace: Optional[str] = fields.workspace,
        page_size: Optional[int] = fields.page_size,
    ) -> EveryskList[Portfolio]:
        result = Portfolio.list(query=query, workspace=workspace, page_size=page_size)
        return result

    @mcp.tool(
        description="Retrieves the details of an existing portfolio by supplying the portfolio's id."
    )
    def portfolio_retrieve(
        id: str = fields.id_, workspace: Optional[str] = fields.workspace
    ) -> Portfolio:
        result = Portfolio.retrieve(id=id, workspace=workspace)
        return result

    @mcp.tool(
        description="Filters a list of portfolios based on the provided criteria."
    )
    def portfolio_filter(
        workspace: Optional[str] = fields.workspace,
        limit: Optional[int] = fields.limit,
        tags: Optional[List[str]] = fields.tags,
        start: Optional[str] = fields.start_date,
        end: Optional[str] = fields.end_date,
        link_uid: Optional[str] = fields.link_uid,
    ) -> EveryskList[Portfolio]:
        result = Portfolio.filter(
            workspace=workspace,
            limit=limit,
            tags=tags,
            start=start,
            end=end,
            link_uid=link_uid,
        )
        return result

    @mcp.tool(
        description="Creates a new portfolio and then returns the created portfolio."
    )
    def portfolio_create(
        name: str = fields.name,
        description: Optional[str] = fields.description,
        tags: List[str] = fields.tags,
        date: Optional[str] = fields.date_portfolio,
        base_currency: Optional[str] = fields.base_currency,
        nlv: Optional[float] = fields.nlv,
        securities: List[Security] = fields.security_list,
        with_securities: Optional[bool] = fields.with_securities,
        workspace: Optional[str] = fields.workspace,
    ) -> Portfolio:
        if not securities:
            raise ValueError("At least one security must be provided in the portfolio.")

        if not isinstance(securities, list):
            raise TypeError("Securities must be a list of Security objects.")

        for security in securities:
            if not isinstance(security, Security):
                raise TypeError(
                    "Each security must be an instance of the Security class."
                )

        securities = [security.model_dump() for security in securities]

        result = Portfolio.create(
            name=name,
            description=description,
            tags=tags,
            date=date,
            base_currency=base_currency,
            nlv=nlv,
            securities=securities,
            with_securities=with_securities,
            workspace=workspace,
        )

        return result
