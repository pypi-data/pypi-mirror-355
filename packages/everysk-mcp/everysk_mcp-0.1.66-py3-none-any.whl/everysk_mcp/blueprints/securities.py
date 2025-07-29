###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from typing import Annotated, Literal, Optional, Union

from everysk.core.datetime.date import Date
from pydantic import BaseModel, Field

from everysk_mcp.fields import securities as fields


###############################################################################
# Implementation
###############################################################################
class BrazilianFutures(BaseModel):
    type: Literal["brazilian_futures"] = Field(default="brazilian_futures", frozen=True)
    ticker: str = fields.ticker_br
    expiration_date: str = fields.expiration_contract
    price: str = fields.price

    def __str__(self) -> str:
        return f"BRFUT:{self.ticker} {self.expiration_date} {self.price}"


class BrazilianFixedIncome(BaseModel):
    type: Literal["brazilian_fixed_income"] = Field(
        default="brazilian_fixed_income", frozen=True
    )
    asset_code: str = fields.asset_code
    price: str = fields.price

    def __str__(self) -> str:
        return f"BRRF:{self.asset_code} {self.price}"

    @property
    def repo_agreement(self) -> str:
        next_business_day = Date.today().nearest_business_day().strftime("%Y%m%d")
        return f"REPO:{self.asset_code} {next_business_day} {self.price}"


class USEquitiesETFsMutualFunds(BaseModel):
    type: Literal["us_equities_etfs_mutual_funds"] = Field(
        default="us_equities_etfs_mutual_funds", frozen=True
    )
    ticker: str = fields.ticker_us

    def __str__(self) -> str:
        return self.ticker


class ForeignEquities(BaseModel):
    type: Literal["foreign_equities"] = Field(default="foreign_equities", frozen=True)
    ticker: str = fields.ticker_foreign_equities
    mic: str = fields.mic

    def __str__(self) -> str:
        return f"{self.ticker}:{self.mic}"


class EquityOptions(BaseModel):
    type: Literal["equity_options"] = Field(default="equity_options", frozen=True)
    ticker: str = fields.ticker_equity_options
    expiration_date: str = fields.expiration_contract
    call_or_put: Literal["C", "P"] = fields.call_or_put
    strike: str = fields.strike_options
    premium: str = fields.premium

    def __str__(self) -> str:
        return f"{self.ticker} {self.expiration_date} {self.call_or_put}{self.strike} {self.premium}"


class FXForward(BaseModel):
    type: Literal["fx_forward"] = Field(default="fx_forward", frozen=True)
    cross_currency: str = fields.cc_fx_forward
    expiration_date: str = fields.expiration_contract
    forward_rate: str = fields.forward_rate

    def __str__(self) -> str:
        return f"{self.cross_currency} {self.expiration_date} {self.forward_rate}"


class FXOptions(BaseModel):
    type: Literal["fx_options"] = Field(default="fx_options", frozen=True)
    cross_currency: str = fields.cc_fx_options
    expiration_date: str = fields.expiration_contract
    forward_rate: str = fields.forward_rate
    call_or_put: Literal["C", "P"] = fields.call_or_put
    strike: str = fields.strike_options
    premium: str = fields.premium

    def __str__(self) -> str:
        return f"{self.cross_currency} {self.expiration_date} {self.forward_rate} {self.call_or_put}{self.strike} {self.premium}"


class Futures(BaseModel):
    type: Literal["futures"] = Field(default="futures", frozen=True)
    contract: str = fields.contract
    expiration_date: str = fields.expiration_contract

    def __str__(self) -> str:
        return f"FUT:{self.contract} {self.expiration_date}"


class FutureOptions(BaseModel):
    type: Literal["future_options"] = Field(default="future_options", frozen=True)
    contract: str = fields.contract
    expiration_date: str = fields.expiration_contract
    call_or_put: Literal["C", "P"] = fields.call_or_put
    strike: str = fields.strike_options
    premium: str = fields.premium

    def __str__(self) -> str:
        return f"FUT: {self.contract} {self.expiration_date} {self.call_or_put}{self.strike} {self.premium}"


class CorporateBonds(BaseModel):
    type: Literal["corporate_bonds"] = Field(default="corporate_bonds", frozen=True)
    ticker: str = fields.ticker_bonds
    maturity_date: str = fields.maturity
    coupon: str = fields.coupon_bonds
    price: str = fields.price_bonds
    rating: Optional[str] = fields.rating

    def __str__(self) -> str:
        out = f"CORP:{self.ticker} {self.maturity_date} {self.coupon} {self.price}"
        if self.rating:
            out += f" {self.rating}"
        return out


class MunicipalBonds(BaseModel):
    type: Literal["municipal_bonds"] = Field(default="municipal_bonds", frozen=True)
    issuer: str = fields.issuer_muni_bonds
    maturity_date: str = fields.maturity
    coupon: str = fields.coupon_bonds
    price: str = fields.price_bonds
    rating: Optional[str] = fields.rating

    def __str__(self) -> str:
        out = f"MUNI:{self.issuer} {self.maturity_date} {self.coupon} {self.price}"
        if self.rating:
            out += f" {self.rating}"

        return out


class ConvertibleBonds(BaseModel):
    type: Literal["convertible_bonds"] = Field(default="convertible_bonds", frozen=True)
    ticker: str = fields.ticker_bonds
    maturity_date: str = fields.maturity
    coupon: str = fields.coupon_bonds
    price: str = fields.price_bonds
    strike: str = fields.strike
    rating: Optional[str] = fields.rating

    def __str__(self) -> str:
        out = f"CONV:{self.ticker} {self.maturity_date} {self.coupon} {self.price} {self.strike}"
        if self.rating:
            out += f" {self.rating}"
        return out


class ConvertiblePreferredBonds(BaseModel):
    type: Literal["convertible_preferred_bonds"] = Field(
        default="convertible_preferred_bonds", frozen=True
    )
    ticker: str = fields.ticker_bonds
    maturity_date: str = fields.maturity
    coupon: str = fields.coupon_bonds
    par: str = fields.par
    price: str = fields.price_bonds
    strike: str = fields.strike
    rating: Optional[str] = fields.rating

    def __str__(self) -> str:
        out = f"CONVP:{self.ticker} {self.maturity_date} {self.coupon} {self.par} {self.price} {self.strike}"
        if self.rating:
            out += f" {self.rating}"
        return out


class ExchangeableBonds(BaseModel):
    type: Literal["exchangeable_bonds"] = Field(
        default="exchangeable_bonds", frozen=True
    )
    issuer_ticker: str = fields.ticker_xbonds_issuer
    maturity_date: str = fields.maturity
    coupon: str = fields.coupon_bonds
    price: str = fields.price_bonds
    strike: str = fields.strike
    target_ticker: str = fields.ticker_xbonds_target
    rating: Optional[str] = fields.rating

    def __str__(self) -> str:
        out = f"EXCH:{self.issuer_ticker} {self.maturity_date} {self.coupon} {self.price} {self.strike} {self.target_ticker}"
        if self.rating:
            out += f" {self.rating}"
        return out


class GovernmentBonds(BaseModel):
    type: Literal["government_bonds"] = Field(default="government_bonds", frozen=True)
    country: str = fields.country_bonds
    maturity_date: str = fields.maturity
    coupon: str = fields.coupon_bonds
    price: str = fields.price_bonds
    rating: Optional[str] = fields.rating

    def __str__(self) -> str:
        out = f"GOV:{self.country} {self.maturity_date} {self.coupon} {self.price}"
        if self.rating:
            out += f" {self.rating}"
        return out


class InterestRateSwaps(BaseModel):
    type: Literal["interest_rate_swaps"] = Field(
        default="interest_rate_swaps", frozen=True
    )
    country: str = fields.country_irs
    maturity_date: str = fields.maturity
    payer_or_receiver: Literal["P", "R"] = fields.payer_or_receiver_irs
    spread: str = fields.spread

    def __str__(self) -> str:
        return f"SWAP:{self.country} {self.maturity_date} {self.payer_or_receiver}{self.spread}"


class CreditDefaultSwaps(BaseModel):
    type: Literal["credit_default_swaps"] = Field(
        default="credit_default_swaps", frozen=True
    )
    ticker: str = fields.ticker_cds
    maturity_date: str = fields.maturity
    payer_or_receiver: Literal["P", "R"] = fields.payer_or_receiver_cds
    spread: str = fields.spread

    def __str__(self) -> str:
        return f"CDS:{self.ticker} {self.maturity_date} {self.payer_or_receiver}{self.spread}"


class TermLoans(BaseModel):
    type: Literal["term_loans"] = Field(default="term_loans", frozen=True)
    ticker: str = fields.ticker_term_loans
    maturity_date: str = fields.maturity
    coupon: str = fields.coupon_term_loans
    price: str = fields.price_term_loans

    def __str__(self) -> str:
        return f"LOAN:{self.ticker} {self.maturity_date} {self.coupon} {self.price}"


class Warrants(BaseModel):
    type: Literal["warrants"] = Field(default="warrants", frozen=True)
    ticker: str = fields.ticker_warrants
    expiration_date: str = fields.expiration_warrants
    ratio: str = fields.ratio
    premium: str = fields.premium
    strike: str = fields.strike_warrants

    def __str__(self) -> str:
        return f"WRNT:{self.ticker} {self.expiration_date} {self.ratio} {self.premium} {self.strike}"


class Margin(BaseModel):
    type: Literal["margin"] = Field(default="margin", frozen=True)
    currency: str = fields.currency

    def __str__(self) -> str:
        return f"MARGIN:{self.currency}"


class Cash(BaseModel):
    type: Literal["cash"] = Field(default="cash", frozen=True)
    currency: str = fields.currency

    def __str__(self) -> str:
        return f"CASH:{self.currency}"


class Indices(BaseModel):
    type: Literal["indices"] = Field(default="indices", frozen=True)
    ticker: str = fields.ticker_indices

    def __str__(self) -> str:
        return f"IND:{self.ticker}"


class IndexOptions(BaseModel):
    type: Literal["index_options"] = Field(default="index_options", frozen=True)
    ticker: str = fields.ticker_index_options
    expiration_date: str = fields.expiration_index_options
    call_or_put: Literal["C", "P"] = fields.call_or_put
    strike: str = fields.strike_options
    premium: str = fields.premium

    def __str__(self) -> str:
        return f"IND:{self.ticker} {self.expiration_date} {self.call_or_put}{self.strike} {self.premium}"


class Repurchase(BaseModel):
    type: Literal["repurchase"] = Field(default="repurchase", frozen=True)
    instrument: Annotated[BrazilianFixedIncome, Field(discriminator="type")]

    def __str__(self) -> str:
        return self.instrument.repo_agreement


class Provision(BaseModel):
    type: Literal["provision"] = Field(default="provision", frozen=True)
    category: Literal["RECEIVABLES", "PAYABLES", "REDEMPTIONS"] = fields.category

    def __str__(self) -> str:
        return f"PROV:{self.category}"


class Symbol(BaseModel):
    """
    Wrapper model representing a financial instrument in the Everysk system.

    The `Symbol` class acts as a discriminated union over various financial instrument types.
    Each instrument is uniquely identified by its `type` field, which serves as the discriminator
    to allow Pydantic to correctly parse and validate the appropriate subclass instance.

    Attributes:
        instrument (Union[...]): A union of supported financial instrument models,
            such as BrazilianFutures, CorporateBonds, FXOptions, Cash, etc.
            The appropriate model is selected based on the 'type' field in the input data.

    Example:
        symbol = Symbol(
            instrument={
                'type': 'brazilian_futures',
                'ticker': 'IND',
                'expiration_date': '20251231',
                'price': '120000'
            }
        )
        print(str(symbol))  # -> 'BRFUT:IND 20251231 120000'
    """

    instrument: Annotated[
        Union[
            BrazilianFutures,
            BrazilianFixedIncome,
            USEquitiesETFsMutualFunds,
            ForeignEquities,
            EquityOptions,
            FXForward,
            FXOptions,
            Futures,
            FutureOptions,
            CorporateBonds,
            MunicipalBonds,
            ConvertibleBonds,
            ConvertiblePreferredBonds,
            ExchangeableBonds,
            GovernmentBonds,
            InterestRateSwaps,
            CreditDefaultSwaps,
            TermLoans,
            Warrants,
            Margin,
            Cash,
            Indices,
            IndexOptions,
            Repurchase,
            Provision,
        ],
        Field(discriminator="type"),
    ]

    def __str__(self):
        return str(self.instrument)


class Security(BaseModel):
    """
    Represents an Everysk security with its associated properties. It is used to validate
    the existence and validity of all required fields for a security in the Everysk system.

    Example usage:

    security = Security(
        id='sec_001',
        symbol=Symbol(
            instrument=BrazilianFutures(
                ticker='IND',
                expiration_date='20251231',
                price='120000'
            )
        ),
        quantity=10.0
    )

    >>> print(future.model_dump())
    >>> {'id': 'sec_001', 'symbol': 'BRFUT:IND 20251231 120000', 'quantity': 10.0}
    """

    id: str = fields.id_
    symbol: Symbol = fields.symbol
    quantity: float = fields.quantity
    isin: Optional[str] = fields.isin
    fx_rate: Optional[float] = fields.fx_rate
    market_price: float = fields.market_price
    market_value: float = fields.market_value

    def model_dump(self, **kwargs):
        """Override the model_dump method to include the symbol as a string in the output."""
        base = super().model_dump(**kwargs)
        base["symbol"] = str(self.symbol)
        return base

    class Config:
        """
        In Pydantic, the Config inner class is used to configure the behavior of the BaseModel.

        By default, Pydantic only allows standard Python types (eg., int, str, float, etc.) and
        other Pydantic models as field types. To use custom classes (like Symbol), arbitrary types
        must be explicitly allowed.
        """

        arbitrary_types_allowed = True
