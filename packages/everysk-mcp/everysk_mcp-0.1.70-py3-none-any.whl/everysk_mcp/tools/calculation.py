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

from everysk.api import Calculation
from mcp.server.fastmcp import FastMCP

from everysk_mcp.blueprints.securities import Security
from everysk_mcp.fields import definitions as fields


###############################################################################
# Implementation
###############################################################################
def validate_input(
    portfolio_id: Optional[str], securities: Optional[List[Security]]
) -> Optional[List[dict]]:
    """
    Validates mutually exclusive parameters: `portfolio_id` or `securities`.

    - Raises a ValueError if both or neither are provided.
    - Validates that `securities`, if provided, is a list of `Security` instances.
    - Returns the serialized list of securities if valid.

    Args:
        portfolio_id (Optional[str]): The ID of the portfolio.
        securities (Optional[List[Security]]): List of Security objects.

    Returns:
        Optional[List[dict]]: A list of serialized Security dicts if `securities` is provided.
    """
    if portfolio_id is not None and securities is not None:
        raise ValueError(
            "You must provide either portfolio_id or securities, but not both."
        )

    if portfolio_id is None and securities is None:
        raise ValueError("You must provide either portfolio_id or securities.")

    if securities is not None:
        if not isinstance(securities, list):
            raise TypeError("Securities must be a list of Security objects.")

        for security in securities:
            if not isinstance(security, Security):
                raise TypeError(
                    "Each security must be an instance of the Security class."
                )

        return [security.model_dump() for security in securities]

    return None


def register_calculation_tools(mcp: FastMCP) -> None:
    """Register all calculation tools with the given MCP instance."""

    @mcp.tool(
        description="The goal of Monte Carlo Risk Attribution is to calculate the contribution to the overall portfolio risk from each security. We use a measure called Marginal Contribution to Total Risk (MCTR) for Monte Carlo Risk Attribution."
    )
    def monte_carlo_risk_attribution(
        portfolio_id: Optional[str] = fields.id_,
        securities: Optional[List[Security]] = fields.security_list,
        date: Optional[str] = fields.date_portfolio,
        base_currency: Optional[str] = fields.base_currency,
        nlv: Optional[float] = fields.nlv,
        horizon: Optional[int] = fields.horizon,
        sampling: Optional[int] = fields.sampling,
        aggregation: Optional[
            Literal[
                "custom",
                "position",
                "country",
                "sector",
                "gics_sector",
                "market_capitalization",
                "liquidity",
                "implied_rating",
                "duration",
                "security_type",
                "security_type_refined",
                "dividend_yield",
                "exposure",
                "currency",
                "fixed_income",
                "total_esg",
            ]
        ] = fields.aggregation,
        projection: Optional[list[str]] = fields.projection,
        volatility_half_life: Optional[int] = fields.volatility_half_life,
        correlation_half_life: Optional[int] = fields.correlation_half_life,
        risk_measure: Optional[Literal["vol", "var", "cvar"]] = fields.risk_measure,
        filter: Optional[str] = fields.filter_,
    ) -> dict:
        securities = validate_input(portfolio_id, securities)

        result = Calculation.riskAttribution(
            portfolio_id=portfolio_id,
            securities=securities,
            date=date,
            base_currency=base_currency,
            nlv=nlv,
            horizon=horizon,
            sampling=sampling,
            aggregation=aggregation,
            projection=projection,
            volatility_half_life=volatility_half_life,
            correlation_half_life=correlation_half_life,
            risk_measure=risk_measure,
            filter=filter,
        )

        return result

    @mcp.tool(
        description="Calculates the delta-adjusted notional exposure of each security, converted to the base currency of the portfolio."
    )
    def exposure(
        portfolio_id: Optional[str] = fields.id_,
        securities: Optional[List[Security]] = fields.security_list,
        date: Optional[str] = fields.date_portfolio,
        base_currency: Optional[str] = fields.base_currency,
        nlv: Optional[float] = fields.nlv,
        sampling: Optional[int] = fields.sampling,
        aggregation: Optional[
            Literal[
                "custom",
                "position",
                "country",
                "sector",
                "gics_sector",
                "market_capitalization",
                "liquidity",
                "implied_rating",
                "duration",
                "security_type",
                "security_type_refined",
                "dividend_yield",
                "exposure",
                "currency",
                "fixed_income",
                "total_esg",
            ]
        ] = fields.aggregation,
        filter: Optional[str] = fields.filter_,
    ):
        securities = validate_input(portfolio_id, securities)

        result = Calculation.exposure(
            portfolio_id=portfolio_id,
            securities=securities,
            date=date,
            base_currency=base_currency,
            nlv=nlv,
            sampling=sampling,
            aggregation=aggregation,
            filter=filter,
        )

        return result

    @mcp.tool(
        description="Calculates the overall portfolio properties with a single API call. Sensitivities, exposures and risk are aggregated from individual securities to a portfolio level."
    )
    def properties(
        portfolio_id: Optional[str] = fields.id_,
        securities: Optional[List[Security]] = fields.security_list,
        date: Optional[str] = fields.date_portfolio,
        base_currency: Optional[str] = fields.base_currency,
        nlv: Optional[float] = fields.nlv,
        horizon: Optional[int] = fields.horizon,
        sampling: Optional[int] = fields.sampling,
        aggregation: Optional[
            Literal[
                "custom",
                "position",
                "country",
                "sector",
                "gics_sector",
                "market_capitalization",
                "liquidity",
                "implied_rating",
                "duration",
                "security_type",
                "security_type_refined",
                "dividend_yield",
                "exposure",
                "currency",
                "fixed_income",
                "total_esg",
            ]
        ] = fields.aggregation,
        projection: Optional[list[str]] = fields.projection,
        volatility_half_life: Optional[int] = fields.volatility_half_life,
        correlation_half_life: Optional[int] = fields.correlation_half_life,
        confidence: Optional[str] = fields.confidence,
    ):
        securities = validate_input(portfolio_id, securities)

        result = Calculation.properties(
            portfolio_id=portfolio_id,
            securities=securities,
            date=date,
            base_currency=base_currency,
            nlv=nlv,
            horizon=horizon,
            sampling=sampling,
            aggregation=aggregation,
            projection=projection,
            volatility_half_life=volatility_half_life,
            correlation_half_life=correlation_half_life,
            confidence=confidence,
        )

        return result

    @mcp.tool(
        description='Calculates greeks for options and various fixed income sensitivities for fixed income securities. Values can be unitized when "compute_notional" is False, or weighted by the notional exposure of the security when "compute_notional" is True.'
    )
    def sensitivity(
        portfolio_id: Optional[str] = fields.id_,
        securities: Optional[List[Security]] = fields.security_list,
        date: Optional[str] = fields.date_portfolio,
        base_currency: Optional[str] = fields.base_currency,
        sensitivity_type: Literal[
            "delta",
            "gamma",
            "theta",
            "vega",
            "duration",
            "effective_duration",
            "macaulay_duration",
            "modified_duration",
            "cs01",
            "dv01",
            "average_life",
            "rolled_average_life",
            "volatility",
        ] = fields.sensitivity_type,
        compute_notional: Optional[bool] = fields.compute_notional,
    ):
        securities = validate_input(portfolio_id, securities)

        result = Calculation.sensitivity(
            portfolio_id=portfolio_id,
            securities=securities,
            date=date,
            base_currency=base_currency,
            sensitivity_type=sensitivity_type,
            compute_notional=compute_notional,
        )

        return result

    @mcp.tool(
        description="Tracking error is the divergence between the price behavior of a position or a portfolio and the price behavior of a benchmark. This is often in the context of a hedge fund, mutual fund, or exchange-traded fund (ETF) that did not work as effectively as intended, creating an unexpected profit or loss."
    )
    def tracking_errors(
        portfolio1: str = fields.id_,
        portfolio2: str = fields.id_,
        weekly: Optional[bool] = fields.weekly,
        EWMA: Optional[bool] = fields.ewma,
        exponential_decay: Optional[float] = fields.exponential_decay,
        nDays: Optional[int] = fields.ndays,
        nWeeks: Optional[int] = fields.nweeks,
    ):
        result = Calculation.marginalTrackingError(
            portfolio1=portfolio1,
            portfolio2=portfolio2,
            weekly=weekly,
            EWMA=EWMA,
            exponential_decay=exponential_decay,
            nDays=nDays,
            nWeeks=nWeeks,
        )

        return result

    @mcp.tool(
        description="Calculates the magnitude of a security's reaction to changes in underlying factors, most often in terms of its price response to other factors."
    )
    def parametric_risk_attribution(
        id: str = fields.id_,
        projection: List[Security] = fields.projection,
        portfolio_id: Optional[str] = fields.id_exclusive,
        securities: Optional[List[Security]] = fields.security_list_exclusive,
        use_cashflow: Optional[bool] = fields.use_cashflow,
        sampling: Optional[int] = fields.sampling,
        confidence: Optional[str] = fields.confidence,
        historical_days: Optional[int] = fields.historical_days,
        exponential_decay: Optional[float] = fields.exponential_decay,
    ):
        securities = validate_input(portfolio_id, securities)

        result = Calculation.parametricRiskAttribution(
            id=id,
            projection=projection,
            portfolio_id=portfolio_id,
            securities=securities,
            use_cashflow=use_cashflow,
            sampling=sampling,
            confidence=confidence,
            historical_days=historical_days,
            exponential_decay=exponential_decay,
        )

        return result

    @mcp.tool(
        description="Stress Test calculates the expected behavior of the portfolio under different scenarios, including extreme events. Everysk API calculates the probabilities of extreme events happening and factors those probabilities into the calculations. For example: it takes into account that correlations and volatility tend to increase in periods of market distress, resulting in large price oscillations for securities.This API call returns 3 main measures for the specific scenario requested, namely: Conditional value at risk at the left tail of the distribution (CVaR-): The average of the worst (1-confidence) percentile outcomes from the forward looking P&L distribution of the portfolio. Expected profit and loss (EV): The average of the full forward looking P&L distribution of the portfolio. Conditional value at risk at the right tail of the distribution (CVaR+): The average of the best (1-confidence) percentile outcomes from the forward looking P&L distribution of the portfolio."
    )
    def stress_test(
        portfolio_id: Optional[str] = fields.id_exclusive,
        securities: Optional[List[Security]] = fields.security_list_exclusive,
        date: Optional[str] = fields.date_portfolio,
        base_currency: Optional[str] = fields.base_currency,
        nlv: Optional[float] = fields.nlv,
        horizon: Optional[int] = fields.horizon,
        sampling: Optional[int] = fields.sampling,
        aggregation: Optional[
            Literal[
                "custom",
                "position",
                "country",
                "sector",
                "gics_sector",
                "market_capitalization",
                "liquidity",
                "implied_rating",
                "duration",
                "security_type",
                "security_type_refined",
                "dividend_yield",
                "exposure",
                "currency",
                "fixed_income",
                "total_esg",
            ]
        ] = fields.aggregation,
        projection: Optional[list[str]] = fields.projection,
        volatility_half_life: Optional[int] = fields.volatility_half_life,
        correlation_half_life: Optional[int] = fields.correlation_half_life,
        shock: Optional[str] = fields.shock,
        magnitude: str = fields.magnitude,
        confidence: Optional[str] = fields.confidence,
        filter: Optional[str] = fields.filter_,
    ):
        securities = validate_input(portfolio_id, securities)

        result = Calculation.stressTest(
            portfolio_id=portfolio_id,
            securities=securities,
            date=date,
            base_currency=base_currency,
            nlv=nlv,
            horizon=horizon,
            sampling=sampling,
            aggregation=aggregation,
            projection=projection,
            volatility_half_life=volatility_half_life,
            correlation_half_life=correlation_half_life,
            shock=shock,
            magnitude=magnitude,
            confidence=confidence,
            filter=filter,
        )

        return result

    # @mcp.tool(description="Calculates the number of days required to unwind a position in the portfolio, considering the liquidity of each asset. This calculation can help in assessing the market risk associated with the portfolio's current composition.")
    # def days_to_unwind():
    #     ...

    # @mcp.tool(description='Calculates sensitivity for each underlying stress scenario. `securities` parameter is not required if `portfolio_id` is being provided.')
    # def underlying_stress_sensitivity():
    #     ...

    # @mcp.tool(description='Retrieves fundamental data.')
    # def fundamentals():
    #     ...

    # @mcp.tool(description='Retrieves backtest statistics by executing a backtest based on the provided parameters. This method internally calls a function to compute backtest statistics and returns a detailed result dict.')
    # def backtestStatistics():
    #     ...

    # NOT TO BE IMPLEMENTED. WILL BE RENAMED TO portfolio_pricer
    # def bond_pricer():
    #     ...
