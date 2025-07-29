###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
from pydantic import Field

###############################################################################
# Implementation
###############################################################################
aggregation = Field(
    default="position",
    description="Aggregation computes individual security exposures and aggregates them according to the supported criteria",
    examples=[
        {"value": "country", "description": "Aggregate by country"},
        {"value": "currency", "description": "Aggregate by currency"},
        {"value": "dividend_yield", "description": "Aggregate by dividend yield"},
        {"value": "duration", "description": "Aggregate by duration"},
        {"value": "exposure", "description": "Aggregate by exposure"},
        {"value": "fixed_income", "description": "Aggregate fixed income securities"},
        {"value": "gics_sector", "description": "Aggregate by GICS sector"},
        {"value": "implied_rating", "description": "Aggregate by implied rating"},
        {"value": "liquidity", "description": "Aggregate by liquidity"},
        {
            "value": "market_capitalization",
            "description": "Aggregate by market capitalization",
        },
        {"value": "position", "description": "Aggregate by position"},
        {"value": "security_type", "description": "Aggregate by security type"},
        {
            "value": "security_type_refined",
            "description": "Refined security type aggregation",
        },
        {"value": "sector", "description": "Aggregate by sector"},
        {"value": "total_esg", "description": "Aggregate total ESG scores"},
    ],
)

base_currency = Field(
    default="USD",
    description="3-letter ISO 4217 code for currency.",
    examples=[
        {"value": "USD", "description": "Base currency of the entity is US Dollar"},
        {"value": "EUR", "description": "Base currency of the entity is Euro"},
        {
            "value": "BRL",
            "description": "Base currency of the entity is Brazilian Real",
        },
    ],
)

compute_notional = Field(
    default=False,
    description="Determines whether sensitivities should be weighted by the notional exposure or unitized. True:Weight sensitivities by notional exposure. False: Unitize sensitivities.",
    examples=[
        {
            "value": True,
            "description": "Compute sensitivities weighted by notional exposure",
        },
        {"value": False, "description": "Compute unitized sensitivities"},
    ],
)

confidence = Field(
    default="95%",
    description="This parameter determines the confidence level for calculating CVaR. Values accepted: 1sigma, 2sigma, 3sigma, 85%, 90%, 95%, 97%, 99%",
    examples=[
        {"value": "90%", "description": "Confidence level of 90%"},
        {"value": "1sigma", "description": "1-sigma confidence level"},
    ],
)

content_type = Field(
    default="text/plain",
    description="A string to identify the file's format.",
    examples=[
        {"value": "text/plain", "description": "Plain text file"},
        {"value": "application/pdf", "description": "PDF file"},
        {"value": "image/png", "description": "PNG image file"},
        {"value": "application/json", "description": "JSON file"},
    ],
)

correlation_half_life = Field(
    default=6,
    description="Half life of correlation information in months: 0 (no decay), 2, 6, 12, 24 or 48.",
    examples=[
        {"value": 0, "description": "No correlation half-life applied"},
        {"value": 2, "description": "Correlation half-life of 2 days"},
        {"value": 6, "description": "Correlation half-life of 6 days"},
    ],
)

data_file = Field(
    description="The content that will be stored inside the file. It must be a text string.",
    examples=[
        {
            "value": "Hello, World!",
            "description": 'A simple text file with the content "Hello, World!"',
        },
    ],
)

data_datastore = Field(
    description="A list of lists representing the data to be stored in the datastore. The first inner list represents the column names, and the subsequent inner lists represent the rows of data. Each inner list should contain values that are either strings, integers, floats, or booleans.",
    examples=[
        {
            "value": [
                ["date", "ticker", "price"],
                ["2023-01-01", "AAPL", 150.0],
                ["2023-01-02", "AAPL", 152.5],
            ],
            "description": "A simple datastore with two columns: date and ticker, and two rows of data.",
        },
        {
            "value": [
                ["name", "age", "is_active"],
                ["Alice", 30, True],
                ["Bob", 25, False],
            ],
            "description": "A datastore with three columns: name, age, and is_active, and two rows of data.",
        },
    ],
)

date = Field(
    default=None,
    description="A string in YYYYMMDD format indicating the date of the data being stored in the entity. If not provided, the current date will be used.",
    examples=[
        {
            "value": "20250101",
            "description": "Data date for the entity is January 1, 2025",
        },
        {
            "value": "20251231",
            "description": "Data date for the entity is December 31, 2025",
        },
        {
            "value": None,
            "description": "No specific date provided, current date will be used",
        },
    ],
)

date_portfolio = Field(
    default=None,
    description="Portfolio date in the format: YYYYMMDD. The Portfolio Date is important because it instructs the API to use the market conditions and security prices prevailing on that date. Therefore, historical portfolios will be calculated without look ahead. In order to run the portfolio using market conditions prevailing today, use null.",
    examples=[
        {
            "value": "20250101",
            "description": "Data date for the portfolio is January 1, 2025",
        },
        {
            "value": "20251231",
            "description": "Data date for the portfolio is December 31, 2025",
        },
        {
            "value": None,
            "description": "No specific date provided, current date will be used",
        },
    ],
)

description = Field(
    description="Provides detailed information about an entity.",
    examples=[
        {
            "value": "This is a sample text file.",
            "description": "A simple text file with a description",
        },
        {
            "value": "Annual financial report for 2023",
            "description": "A PDF report with a detailed description",
        },
        {
            "value": "This datastore contains financial data for analysis.",
            "description": "A simple description for the datastore",
        },
        {
            "value": "Datastore for storing historical stock prices and trading volumes",
            "description": "A detailed description for the datastore",
        },
        {
            "value": "This portfolio contains financial data for analysis.",
            "description": "A simple description for the portfolio",
        },
        {
            "value": "Portfolio for storing historical stock prices and trading volumes",
            "description": "A detailed description for the portfolio",
        },
    ],
)

end_date = Field(
    default=None,
    description="The end date for filtering entities, in YYYYMMDD format.",
    examples=[
        {
            "value": "20251231",
            "description": "Filter entities created on or before December 31, 2025",
        },
        {"value": None, "description": "No end date filtering applied"},
    ],
)

ewma = Field(
    default=False,
    description="If True, the exponentially weighted moving average will be applied to volatilities.",
    examples=[
        {"value": True, "description": "Use exponentially weighted moving average"},
        {"value": False, "description": "Use simple average"},
    ],
)

exponential_decay = Field(
    default=0.94,
    description='Weighting factor determining the rate at which "older" data enter into the calculation of the EWMA. It accepts float values from 0 to 1. This parameter is only used when EWMA is True.',
    examples=[
        {"value": 0.94, "description": "Exponential decay factor of 0.94"},
        {"value": 0.90, "description": "Exponential decay factor of 0.90"},
    ],
)

filter_ = Field(
    default=None,
    description="Filters are powerful constructs to return the unique identifiers of certain positions in the portfolio, satisfying a specific criteria. When used, they isolate the behavior of a unique group, compared to the whole. For example: how illiquid securities might react to an oil shock. When present it runs a pre-processing calculation to select identifiers that satisfy certain criteria. It can be used to highlight the properties of a subset of the portfolio, for example: only fixed income securities. Calculations are performed for the whole portfolio and only displayed for the securities that satisfy the filter.",
    examples=[
        {
            "value": "exposure('long') and currency('foreign securities')",
            "description": "Example using logical operator 'and'. Retrieve identifiers for positions that are long and also denominated in a currency different than the base currency of the portfolio",
        },
        {
            "value": "exposure('short') or liquidity('>300%')",
            "description": "Example using logical operator 'or'. Retrieve any shorts or illiquid positions",
        },
        {
            "value": "not(type('equity option long delta'))",
            "description": "Example using logical operator 'not'. Retrieve all positions that are not long options",
        },
        {
            "value": "currency('foreign securities') and (not(exposure('short') or liquidity('>300%')))",
            "description": "Example using logical operators combined",
        },
        {"value": None, "description": "Use the whole portfolio"},
    ],
)

historical_days = Field(
    default=252,
    description="Number of business days used to calculate the covariance for the primitive risk factors: 0 (no decay), 2, 6, 12, 24 or 48.",
    examples=[
        {
            "value": 252,
            "description": "Calculate risk attribution over the last 252 trading days",
        },
        {
            "value": 30,
            "description": "Calculate risk attribution over the last 30 trading days",
        },
    ],
)

horizon = Field(
    default=5,
    description="Simulates the behavior of each security via their underlying risk factors. It accepts: 1, 5, 20 or 60",
    examples=[
        {"value": 1, "description": "Simulate risk attribution for 1 day"},
        {"value": 5, "description": "Simulate risk attribution for 5 days"},
    ],
)

id_ = Field(
    description="A unique identifier (UID) for an entity.",
    examples=[
        {
            "value": "dats_52KiJy2yFvosTtWM5aUJcOs1R",
            "description": "A datastore's id will always look like this.",
        },
        {
            "value": "file_52KiJy2yFvosTtWM5aUJcOs1R",
            "description": "A file's id will always look like this.",
        },
        {
            "value": "port_52KiJy2yFvosTtWM5aUJcOs1R",
            "description": "A portfolio's id will always look like this.",
        },
        {
            "value": "repo_52KiJy2yFvosTtWM5aUJcOs1R",
            "description": "A report's id will always look like this.",
        },
        {
            "value": "rtpl_52KiJy2yFvosTtWM5aUJcOs1R",
            "description": "A report template's id will always look like this.",
        },
        {
            "value": "wrkf_1hud1QQNR2z7m9IPLrSylpOMN",
            "description": "A workflow's id will always look like this.",
        },
        {
            "value": "wfex_N4buYFKsRDtlvavf3TvnnCkCh",
            "description": "An execution's id will always look like this.",
        },
    ],
)

id_exclusive = Field(
    default=None,
    description="It is the ID of and existing portfolio. When passing a portfolio's ID as parameter the calculation will be performed using the given portfolio's securities, date, base currency and nlv. The securities parameter is no longer required.",
    examples=[
        {
            "value": "port_52KiJy2yFvosTtWM5aUJcOs1R",
            "description": "A portfolio's id will always look like this.",
        }
    ],
)

limit = Field(
    default=100,
    description="The maximum number of entities to retrieve.",
    examples=[
        {"value": 100, "description": "Default limit, returns up to 100 entities"},
        {"value": 50, "description": "Returns up to 50 entities"},
    ],
)

link_uid = Field(
    default=None,
    description="A unique identifier (UID) for a link associated with the entity. If provided, only entities linked to this UID will be returned.",
    examples=[
        {
            "value": "link_1234567890abcdef",
            "description": "Filter by a specific link UID",
        },
        {"value": None, "description": "No link UID filtering applied"},
    ],
)

magnitude = Field(
    default="-0.10",
    description="The magnitude of the shock. The parameter magnitude is an instantaneous shock as a decimal number: -10% = -0.10. Certain rates/spreads can also be shocked and the magnitude of the shock is an absolute widening or tightening of the rate/spread. Example 1: Shock: IND: SPX | Magnitude: -1% | Current level: 2821| New level: 2792. Example 2: Shock: IND: LIBOR3M | Magnitude: -1% | Current level: 1.77| New level: 0.77. In these examples, the shock in SPX is a percent change, whereas the libor shock is an absolute shift.",
    examples=[
        {"value": "-0.05", "description": "Apply a 5 percent shock"},
        {"value": "-0.10", "description": "Apply a 10 percent shock"},
    ],
)

name = Field(
    description="A string to identify an entity besides its id. Feel free to use a meaningful name.",
    examples=[
        {"value": "my_file.txt", "description": "A simple text file named my_file.txt"},
        {"value": "report.pdf", "description": "A PDF report file named report.pdf"},
        {
            "value": "my_datastore",
            "description": "A simple datastore named my_datastore",
        },
        {
            "value": "financial_data_datastore",
            "description": "A datastore containing financial data",
        },
        {
            "value": "my_portfolio",
            "description": "A simple portfolio named my_portfolio",
        },
        {
            "value": "financial_data_portfolio",
            "description": "A portfolio containing financial data",
        },
    ],
)

ndays = Field(
    default=252,
    description="Number of historical business days used in calculation when weekly is False.",
    examples=[
        {
            "value": 252,
            "description": "Calculate tracking error over the last 252 trading days",
        },
        {
            "value": 30,
            "description": "Calculate tracking error over the last 30 trading days",
        },
    ],
)

nlv = Field(
    default=None,
    description="The net liquidating value of the entity (also called NAV). When not supplied by user, the API will calculate the net liquidating value of all the cash securities. Securities traded on margin are assumed to have NLV zero. Supplying an NLV effectively reconciles the margin.",
    examples=[
        {
            "value": 100000.0,
            "description": "Net Liquidation Value of the entity is $100,000.00",
        },
        {
            "value": None,
            "description": "No NLV provided, it will be calculated based on the securities",
        },
    ],
)

nweeks = Field(
    default=200,
    description="Number of historical weeks used in calculation when weekly is True.",
    examples=[
        {
            "value": 200,
            "description": "Calculate tracking error over the last 200 weeks",
        },
        {"value": 52, "description": "Calculate tracking error over the last 52 weeks"},
    ],
)

operation = Field(
    description='Type of operation to be performed, either "buy" or "sell".',
)

page_size = Field(
    default=100,
    description="Set the number of entities that will be listed per page.",
    examples=[
        {
            "value": 100,
            "description": "Default page size, returns 100 entities per page",
        },
        {"value": 50, "description": "Returns 50 entities per page"},
    ],
)

parameters = Field(
    default={},
    description="Object sent to be used inside the workflow that will be started through the API. Usually this object contains information and data required by the workers inside the workflow in order to execute properly. If the workers inside the target workflow do not require external inputs you can pass a empty object as parameter.",
    examples=[
        {
            "value": {"param1": "value1", "param2": 42},
            "description": "Parameters to be passed to the workflow",
        },
        {
            "value": {},
            "description": "No parameters provided, using default values if available",
        },
    ],
)

projection = Field(
    default=["IND:SPX"],
    description="User supplied array of securities to be used as a top-down factor model. Maximum number of elements in the projection array is 15.",
    examples=[
        {"value": ["IND:SPX"], "description": "Projection using the S&P 500 index"},
        {
            "value": ["IND:NDX", "IND:DJI"],
            "description": "Projection using multiple indices",
        },
    ],
)

quantity = Field(description="Quantity of the security to be traded")

query = Field(
    default=None,
    description="Request a list of entities filtering it by `name` or `tag`. When using a `tag` to perform a query, each term must include a hashtag prefix.",
    examples=[
        {"value": None, "description": "Return all entities"},
        {"value": "my-entity", "description": "Filter by entity name"},
        {
            "value": "#tag1 #tag2",
            "description": "Filter by tags, each tag must start with a hashtag.",
        },
    ],
)

risk_measure = Field(
    default="vol",
    description="Specifies the forward looking portfolio risk property being measured by MCTR. vol: forward looking annualized volatility of the P&L distribution for the portfolio. var: Value-at-Risk of the P&L distribution for the portfolio. cvar: Conditional Value-at-Risk of the P&L distribution for the portfolio.",
    examples=[
        {"value": "vol", "description": "Calculate volatility"},
        {"value": "var", "description": "Calculate value at risk"},
        {"value": "cvar", "description": "Calculate conditional value at risk"},
    ],
)

sampling = Field(
    default=1,
    description="Sampling represents the frequency that historical prices and rates (spreads) are collected in order to compute the invariant risk factors. In order to sample daily, use 1. In order to sample weekly (non-overlapping), pass 5. It accepts: 1 or 5.",
    examples=[
        {"value": 1, "description": "Sample daily"},
        {"value": 5, "description": "Sample weekly (non-overlapping)"},
    ],
)

security_ticker = Field(
    description="Ticker of the security to be traded",
)

security_list = Field(
    description="It is an array of securities to describe the securities in the portfolio. Each object represents a security with a unique id, symbol, quantity",
)

security_list_exclusive = Field(
    default=None,
    description="It is an array describing the securities in the portfolio. Not required if portfolio_id is being provided.",
)

sensitivity_type = Field(
    default="delta",
    description="The type of sensitivity to be calculated.",
    examples=[
        {"value": "average_life", "description": "Calculate average life sensitivity"},
        {
            "value": "cs01",
            "description": "Calculate CS01 (Credit Spread 01) sensitivity",
        },
        {"value": "delta", "description": "Calculate delta sensitivity"},
        {"value": "duration", "description": "Calculate duration sensitivity"},
        {
            "value": "dv01",
            "description": "Calculate DV01 (dollar value of 01) sensitivity",
        },
        {
            "value": "effective_duration",
            "description": "Calculate effective duration sensitivity",
        },
        {"value": "gamma", "description": "Calculate gamma sensitivity"},
        {
            "value": "macaulay_duration",
            "description": "Calculate Macaulay duration sensitivity",
        },
        {
            "value": "modified_duration",
            "description": "Calculate modified duration sensitivity",
        },
        {
            "value": "rolled_average_life",
            "description": "Calculate rolled average life sensitivity",
        },
        {"value": "theta", "description": "Calculate theta sensitivity"},
        {"value": "vega", "description": "Calculate vega sensitivity"},
        {"value": "volatility", "description": "Calculate volatility sensitivity"},
    ],
)

shock = Field(
    default="IND:SPX",
    description="The security being used for the stress test.",
    examples=[
        {"value": "IND:SPX", "description": "Apply a shock to the S&P 500 index"},
        {"value": "IND:NDX", "description": "Apply a shock to the NASDAQ-100 index"},
    ],
)

synchronous = Field(
    default=True,
    description="When True, the workflow will be run synchronously, meaning the API will wait for the workflow to finish before returning the result. When False, the workflow will be run asynchronously, and the API will return immediately with a reference to the workflow execution.",
    examples=[
        {
            "value": True,
            "description": "Run the workflow synchronously, waiting for it to finish",
        },
        {
            "value": False,
            "description": "Run the workflow asynchronously, returning immediately",
        },
    ],
)

start_date = Field(
    default=None,
    description="The start date for filtering entities, in YYYYMMDD format.",
    examples=[
        {
            "value": "20250101",
            "description": "Filter entities created on or after January 1, 2025",
        },
        {"value": None, "description": "No start date filtering applied"},
    ],
)

tags = Field(
    default=[],
    description="Sequence of hashtags used to label or filter the related entity. Any sequence of lowercase character, numbers and underscore might be used.",
    examples=[
        {"value": ["tag1", "tag2"], "description": "Filter by multiple tags"},
        {"value": [], "description": "No tag filtering applied"},
    ],
)

use_cashflow = Field(
    default=True,
    description="For fixed income securities, when True, maps each cashflow event (interest, principal amortization) to various key points in the respective interest rate curve. When flag is False, it uses the Macaulay duration to map bond price to neighboring key points in the respective interest rate curve.",
    examples=[
        {"value": True, "description": "Use cashflow data for risk attribution"},
        {
            "value": False,
            "description": "Use current market prices for risk attribution",
        },
    ],
)

volatility_half_life = Field(
    default=2,
    description="Half life of volatility information in months: 0 (no decay), 2, 6, 12, 24 or 48.",
    examples=[
        {"value": 0, "description": "No volatility half-life applied"},
        {"value": 2, "description": "Volatility half-life of 2 days"},
        {"value": 6, "description": "Volatility half-life of 6 days"},
    ],
)

weekly = Field(
    default=True,
    description="The Calculation API will use weekly return to calculate the tracking error.",
    examples=[
        {"value": True, "description": "Calculate weekly tracking error"},
        {"value": False, "description": "Calculate daily tracking error"},
    ],
)

with_data = Field(
    default=True,
    description="When True, the the data inside the entity will be returned in the api response.",
    examples=[
        {"value": True, "description": "Return the entity with its data included"},
        {"value": False, "description": "Return the entity without its data"},
    ],
)

with_securities = Field(
    default=True,
    description="When True, the securities inside the entity will be returned in the api response.",
    examples=[
        {
            "value": True,
            "description": "Return the entity with its securities included",
        },
        {"value": False, "description": "Return the entity without its securities"},
    ],
)

workspace = Field(
    default="main",
    description="Determines on which workspace the request will be made. Default is `main`.",
    examples=[
        {"value": "main", "description": "Default workspace"},
        {
            "value": "my-workspace",
            "description": "A custom workspace where the files are listed",
        },
    ],
)
