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

### Parameters ################################################################
id_ = Field(description="A unique identifier (UID) for a security.")

symbol = Field(description="Security symbol, according to Everysk's custom symbology")

quantity = Field(
    description="Numbers of shares or contracts. Positive quantities are longs and negative are shorts. For fixed income securities, mutual funds, swaps, cash and margin the amounts are defined in the security's currency.",
)

isin = Field(
    default=None,
    description="International Securities Identification Number (ISIN) for the security. This is an optional field and may not be available for all securities.",
    examples=[
        {"value": "US0378331005", "description": "ISIN for Apple Inc."},
        {"value": "US5949181045", "description": "ISIN for Microsoft Corporation"},
        {"value": None, "description": "No ISIN available for this security"},
    ],
)

fx_rate = Field(
    default=None,
    description="The price of the domestic currency stated in terms of another currency.",
)

market_price = Field(description="Current market price in local currency.")

market_value = Field(
    description="Current market value in local currency, calculated as `quantity * market_price`.",
)

### Asset code ################################################################
asset_code = Field(
    description="Ticker of brazilian asset code",
    examples=[
        {"value": "NTNB_20251231", "description": "Ticker for a NTN-B"},
        {"value": "NTNC_20251231", "description": "Ticker for a NTN-C"},
        {"value": "NTNF_20251231", "description": "Ticker for a NTN-F"},
        {"value": "LTN_20251231", "description": "Ticker for a LTN"},
        {"value": "LFT_20251231", "description": "Ticker for a LFT"},
        {"value": "BSA325", "description": "Ticker for a private debenture"},
        {"value": "CRA020001E5", "description": "Ticker for a CRA"},
        {"value": "LFSC1900081", "description": "Ticker for a LF"},
        {"value": "CDB017OBJWK", "description": "Ticker for a CDB"},
    ],
)

### Call or Put ###############################################################
call_or_put = Field(
    description="Indicates whether the option is a call or put option.",
    examples=[
        {"value": "C", "description": "This is a call option"},
        {"value": "P", "description": "This is a put option"},
    ],
)

### Category ##################################################################
category = Field(
    description="Type of provision, which can be RECEIVABLES, PAYABLES or REDEMPTIONS.",
    examples=[
        {"value": "RECEIVABLES", "description": "This is a receivables provision"},
        {"value": "PAYABLES", "description": "This is a payables provision"},
        {"value": "REDEMPTIONS", "description": "This is a redemptions provision"},
    ],
)

### Contract ##################################################################
contract = Field(
    description="Label for underlying future contract ",
    examples=[
        {"value": "CL", "description": "Crude Oil Futures"},
        {"value": "NG", "description": "Natural Gas Futures"},
    ],
)

### Country ###################################################################
country_bonds = Field(
    description='ISO code for the country of the government bond. For example, "US" for United States, "BR" for Brazil.',
    examples=[
        {
            "value": "US",
            "description": "US is the ISO code for United States government bonds",
        },
        {
            "value": "BR",
            "description": "BR is the ISO code for Brazilian government bonds",
        },
        {
            "value": "DE",
            "description": "DE is the ISO code for German government bonds",
        },
        {
            "value": "JP",
            "description": "JP is the ISO code for Japanese government bonds",
        },
    ],
)

country_irs = Field(
    description="ISO Code for the issuer government (US only).",
    examples=[
        {
            "value": "US",
            "description": "US is the ISO code for United States interest rate swaps",
        }
    ],
)

### Coupon ####################################################################
coupon_bonds = Field(
    description="The coupon rate of the bond, expressed as a percentage.",
    examples=[
        {"value": "5.25", "description": "Coupon rate of the bond is 5.25%"},
        {"value": "10.00", "description": "Coupon rate of the bond is 10.00%"},
    ],
)

coupon_term_loans = Field(
    description="The spread over Libor for the loan, expressed as a percent amount.",
    examples=[
        {
            "value": "5.25",
            "description": "Spread over Libor for the term loan is 5.25%",
        },
        {
            "value": "10.00",
            "description": "Spread over Libor for the term loan is 10.00%",
        },
    ],
)

### Cross currency ############################################################
cc_fx_forward = Field(
    description="ISO code for the cross currency pair. Users can define any combination.",
    examples=[
        {"value": "MXNUSD", "description": "Mexican Peso to US Dollar"},
        {"value": "EURAUD", "description": "Euro to Australian Dollar"},
    ],
)

cc_fx_options = Field(
    description="ISO code for the cross currency pair. Users can define any combination. The option symbology is always in reference to the first currency, so a put on MXNUSD is a put on Mexican peso, call on US dollar.",
    examples=[
        {"value": "MXNUSD", "description": "Mexican Peso to US Dollar"},
        {"value": "EURAUD", "description": "Euro to Australian Dollar"},
    ],
)

### Currency ##################################################################
currency = Field(
    description="ISO code for the currency of the cash account.",
    examples=[
        {"value": "USD", "description": "US Dollar"},
        {"value": "EUR", "description": "Euro"},
        {"value": "BRL", "description": "Brazilian Real"},
    ],
)

### Expiration date ###########################################################
expiration_contract = Field(
    description="String in YYYYMMDD format indicating the expiration date for the contract.",
    examples=[
        {
            "value": "20250101",
            "description": "Expiration date for the contract is January 1, 2025",
        },
        {
            "value": "20251231",
            "description": "Expiration date for the contract is December 31, 2025",
        },
    ],
)

expiration_index_options = Field(
    description="String in YYYYMMDD format indicating the expiration date for the option.",
    examples=[
        {
            "value": "20250101",
            "description": "Expiration date for the index option is January 1, 2025",
        },
        {
            "value": "20251231",
            "description": "Expiration date for the index option is December 31, 2025",
        },
    ],
)

expiration_warrants = Field(
    description="String in YYYYMMDD format indicating the expiration date for the warrant.",
    examples=[
        {
            "value": "20250101",
            "description": "Expiration date for the warrant is January 1, 2025",
        },
        {
            "value": "20251231",
            "description": "Expiration date for the warrant is December 31, 2025",
        },
    ],
)

### Forward rate ##############################################################
forward_rate = Field(
    description="Indicates the contracted exchange rate.",
    examples=[
        {
            "value": "0.045",
            "description": "This quantity is always in respect with the first currency in the pair. Thus, for MXNUSD, 0.045 with a quantity of -40e6 means that 40 milllion of Mexican pesos are to be exchanged by 1.8 million US dollars on the specified date.",
        }
    ],
)

### Issuer ####################################################################
issuer_muni_bonds = Field(
    description="Ticker for issuer of bond (US only).",
    examples=[
        {"value": "PA", "description": "Ticker for Pennsylvania"},
    ],
)

### Maturity date #############################################################
maturity = Field(
    description="String in YYYYMMDD format indicating the maturity date for the security.",
    examples=[
        {
            "value": "20250101",
            "description": "Maturity date for the security is January 1, 2025",
        },
        {
            "value": "20251231",
            "description": "Maturity date for the security is December 31, 2025",
        },
    ],
)

### MIC #######################################################################
mic = Field(
    description="Market Identifier Code (MIC) is the ISO code for the global exchange.",
    examples=[
        {"value": "XETR", "description": "MIC for Frankfurt Stock Exchange"},
        {"value": "XTKS", "description": "MIC for Tokyo Stock Exchange"},
        {"value": "BVMF", "description": "MIC for B3 (Brazilian Stock Exchange)"},
    ],
)

### Par #######################################################################
par = Field(
    description="The par value of the convertible preferred bond, which is the face value of the bond.",
    examples=[
        {
            "value": "100",
            "description": "Par value of the convertible preferred bond is $100.00",
        },
        {
            "value": "105.5",
            "description": "Par value of the convertible preferred bond is $105.50",
        },
    ],
)

### Payer or Receiver #########################################################
payer_or_receiver_irs = Field(
    description="P indicates a payer swap (pay fixed/receive floating) /  R indicates a receiver swap (receive fixed/pay floating)",
    examples=[
        {"value": "P", "description": "This is a payer swap"},
        {"value": "R", "description": "This is a receiver swap"},
    ],
)

payer_or_receiver_cds = Field(
    description="P indicates a payer CDS (pay premium/receive protection) /  R indicates a receiver CDS (receive premium/pay protection)",
    examples=[
        {"value": "P", "description": "This is a payer CDS"},
        {"value": "R", "description": "This is a receiver CDS"},
    ],
)

### Premium ###################################################################
premium = Field(
    description="The premium of the contract, which is the price paid for it.",
    examples=[
        {"value": "5.25", "description": "Premium of the contract is $5.25"},
        {"value": "10.00", "description": "Premium of the contract is $10.00"},
    ],
)

### Price #####################################################################
price = Field(
    description="The asset price.",
    examples=[
        {"value": "5.25", "description": "Unit price of the asset is $5.25"},
        {"value": "10.00", "description": "Unit price of the asset is $10.00"},
    ],
)

price_bonds = Field(
    description="The price of the bond, provided as an absolute price, not percent of par.",
    examples=[
        {"value": "100", "description": "Price of the bond is $100.00"},
        {"value": "105.5", "description": "Price of the bond is $105.50"},
    ],
)

price_term_loans = Field(
    description="The price of the term loan, provided as an absolute price, not percent of par.",
    examples=[
        {"value": "100", "description": "Price of the term loan is $100.00"},
        {"value": "105.5", "description": "Price of the term loan is $105.50"},
    ],
)

### Rating ####################################################################
rating = Field(
    default=None,
    description="The bond rating formatted in S&P rating syntax e.g., AA, BBB+, etc. Used when the issuer curve is not available or multiple ratings exist for an issuer.",
    examples=[
        {"value": "AA", "description": "Credit rating of the convertible bond is AA"},
        {"value": None, "description": "No credit rating available for this bond"},
    ],
)

### Ratio #####################################################################
ratio = Field(
    description="Indicates the number of common shares per warrant upon conversion.",
    examples=[
        {
            "value": "1",
            "description": "One warrant allows the purchase of one share of the underlying stock",
        },
        {
            "value": "0.5",
            "description": "One warrant allows the purchase of half a share of the underlying stock",
        },
    ],
)

### Spread ####################################################################
spread = Field(
    description="The spread of the swap, expressed as a percentage.",
    examples=[
        {"value": "0.25", "description": "Spread of the swap is 0.25%"},
        {"value": "0.50", "description": "Spread of the swap is 0.50%"},
    ],
)

### Strike ####################################################################
strike = Field(
    description="The strike price of the bond, which is the price at which it can be converted.",
    examples=[
        {"value": "150", "description": "Strike price of the bond is $150.00"},
        {"value": "120", "description": "Strike price of the bond is $120.00"},
    ],
)

strike_options = Field(
    description="The strike of the option contract, which is the price at which the option can be exercised.",
    examples=[
        {
            "value": "150",
            "description": "Strike price of the option contract is $150.00",
        },
        {
            "value": "120",
            "description": "Strike price of the option contract is $120.00",
        },
    ],
)

strike_warrants = Field(
    description="The strike price of the warrant, which is the price at which the warrant can be exercised.",
    examples=[
        {"value": "150", "description": "Strike price of the warrant is $150.00"},
        {"value": "120", "description": "Strike price of the warrant is $120.00"},
    ],
)

### Ticker ####################################################################
ticker_br = Field(
    description="Ticker of brazilian asset code",
    examples=[
        {
            "value": "AFS",
            "description": "AFS is the ticker for the South African Rand Future",
        },
        {
            "value": "DAP",
            "description": "DAP is the ticker for the ID x IPCA coupon Future",
        },
        {"value": "DDI", "description": "DDI is the ticker for the Selic Rate Future"},
        {"value": "DI1", "description": "DI1 is the ticker for the DI Rate Future"},
        {
            "value": "IND",
            "description": "IND is the ticker for the Ibovespa Index Future",
        },
        {
            "value": "ISP",
            "description": "ISP is the ticker for the S&P500 Index Future",
        },
        {
            "value": "OC1",
            "description": "OC1 is the ticker for the IDI x U.S. Dollar Spread Future",
        },
        {
            "value": "WIN",
            "description": "WIN is the ticker for the Mini Ibovespa Index Future",
        },
        {
            "value": "WSP",
            "description": "WSP is the ticker for the Mini S&P500 Index Future",
        },
        {
            "value": "CNH",
            "description": "CNH is the ticker for the Chinese Iuan (Type A) Future",
        },
        {"value": "DOL", "description": "DOL is the ticker for the US Dollar Future"},
        {
            "value": "GBR",
            "description": "GBR is the ticker for the Sterling Pound Future",
        },
        {
            "value": "EUP",
            "description": "EUP is the ticker for the Euro (Type B) Future",
        },
        {"value": "EUR", "description": "EUR is the ticker for the Euro Future"},
        {"value": "IAP", "description": "IAP is the ticker for the IPCA Spread Future"},
        {
            "value": "JAP",
            "description": "JAP is the ticker for the Japanese Yen Future",
        },
        {
            "value": "WDO",
            "description": "WDO is the ticker for the Mini US Dollar Future",
        },
        {
            "value": "AUS",
            "description": "AUS is the ticker for the Australian Dollar Future",
        },
        {
            "value": "CAN",
            "description": "CAN is the ticker for the Canadian Dollar Future",
        },
        {
            "value": "CHL",
            "description": "CHL is the ticker for the Chilean Peso Future",
        },
        {
            "value": "CNY",
            "description": "CNY is the ticker for the Chinese Iuan Future",
        },
        {
            "value": "MEX",
            "description": "MEX is the ticker for the Mexican Peso Future",
        },
        {
            "value": "NOK",
            "description": "NOK is the ticker for the Norwegian krone Future",
        },
        {
            "value": "RUB",
            "description": "RUB is the ticker for the Russian Ruble Future",
        },
        {"value": "SWI", "description": "SWI is the ticker for the Swiss Franc Future"},
        {
            "value": "TUQ",
            "description": "TUQ is the ticker for the Turkish Pound Future",
        },
    ],
)

ticker_bonds = Field(
    description="Ticker for issuer of bond (US only).",
    examples=[
        {"value": "NFLX", "description": "Ticker for Netflix, Inc."},
        {"value": "COMM", "description": "Ticker for Comcast Corporation"},
    ],
)

ticker_cds = Field(
    description="Ticker for the company credit protection is being bought/sold (US only).",
    examples=[
        {"value": "NFLX", "description": "Ticker for Netflix, Inc."},
        {"value": "COMM", "description": "Ticker for Comcast Corporation"},
    ],
)

ticker_equity_options = Field(
    description=" Simple ticker for US exchanges or ticker and exchange (MIC) for global equities.",
    examples=[
        {
            "value": "IBM",
            "description": "Ticker for International Business Machines Corporation",
        },
        {
            "value": "PETR3:BVMF",
            "description": "Ticker and MIC for Petrobras S.A. on B3",
        },
    ],
)

ticker_xbonds_issuer = Field(
    description="Ticker for issuer of exchangeable bond (US only).",
    examples=[
        {"value": "NFLX", "description": "Ticker for Netflix, Inc."},
        {"value": "COMM", "description": "Ticker for Comcast Corporation"},
    ],
)

ticker_xbonds_target = Field(
    description="Ticker for the target company of the exchangeable bond (the company the bond can be converted into).",
    examples=[
        {
            "value": "AAPL",
            "description": "Ticker for Apple Inc., the target company of the exchangeable bond",
        },
        {
            "value": "GOOGL",
            "description": "Ticker for Alphabet Inc., the target company of the exchangeable bond",
        },
    ],
)

ticker_foreign_equities = Field(
    description="Ticker of foreign asset code.",
    examples=[
        {"value": "SIE", "description": "Ticker for Siemens AG on XETRA"},
        {
            "value": "6758",
            "description": "Ticker for Sony Group Corporation on Tokyo Stock Exchange",
        },
        {"value": "PETR3", "description": "Ticker for Petrobras S.A. on B3"},
    ],
)

ticker_index_options = Field(
    description="Ticker for the index option.",
    examples=[
        {"value": "SPX", "description": "S&P 500 Index Option"},
        {"value": "NDX", "description": "NASDAQ-100 Index Option"},
        {"value": "DJI", "description": "Dow Jones Industrial Average Option"},
    ],
)

ticker_indices = Field(
    description="Ticker for the index.",
    examples=[
        {"value": "SPX", "description": "S&P 500 Index"},
        {"value": "NDX", "description": "NASDAQ-100 Index"},
        {"value": "DJI", "description": "Dow Jones Industrial Average"},
    ],
)

ticker_term_loans = Field(
    description="Ticker for the company that issued the term loan (US only).",
    examples=[
        {"value": "NFLX", "description": "Ticker for Netflix, Inc."},
        {"value": "COMM", "description": "Ticker for Comcast Corporation"},
    ],
)

ticker_us = Field(
    description="Ticker of US asset code. For securities listed in the US exchanges (XNAS, XNYS, ARCX, XASE) the MIC - Market Identification Code - is not necessary.",
    examples=[
        {"value": "AAPL", "description": "Ticker for Apple Inc."},
        {
            "value": "IBM",
            "description": "Ticker for International Business Machines Corporation",
        },
        {"value": "USO", "description": "Ticker for United States Oil Fund"},
        {
            "value": "BAGIX",
            "description": "Ticker for Baird Aggregate Bond Index Fund Institutional Class",
        },
    ],
)

ticker_warrants = Field(
    description="Simple Ticker for US exchanges.",
    examples=[
        {"value": "EXXIW", "description": "Ticker for the warrant on EXXI"},
    ],
)
