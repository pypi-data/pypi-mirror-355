import logging
from datetime import datetime
from typing import Literal
import sys

import pandas as pd
try:
    import talib  # type: ignore
    _ta_available = True
except ImportError:
    _ta_available = False
from mcp.server.fastmcp import FastMCP
from tabulate import tabulate
from yfinance.exceptions import YFRateLimitError

from . import yfinance_utils
from . import cnn_fng_utils

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)


mcp = FastMCP("Investor-Agent", dependencies=["yfinance", "httpx", "pandas"]) # TA-Lib is optional


@mcp.tool()
def get_ticker_data(ticker: str) -> str:
    """Get comprehensive report for ticker: overview, news, metrics, performance, dates, analyst recommendations, and upgrades/downgrades."""
    try:
        info = yfinance_utils.get_ticker_info(ticker)
        if not info:
            return f"No information available for {ticker}"

        sections = []

        # Company overview
        overview = [
            ["Company Name", info.get('longName', 'N/A')],
            ["Sector", info.get('sector', 'N/A')],
            ["Industry", info.get('industry', 'N/A')],
            ["Market Cap", f"${info.get('marketCap', 0):,.2f}" if info.get('marketCap') else "N/A"],
            ["Employees", f"{info.get('fullTimeEmployees', 0):,}" if info.get('fullTimeEmployees') else "N/A"],
            ["Beta", f"{info.get('beta', 0):.2f}" if info.get('beta') else "N/A"]
        ]
        sections.extend(["COMPANY OVERVIEW", tabulate(overview, tablefmt="plain")])

        # Key metrics
        metrics = [
            ["Current Price", f"${info.get('currentPrice', 0):.2f}" if info.get('currentPrice') else "N/A"],
            ["52-Week Range", f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}" if info.get('fiftyTwoWeekLow') and info.get('fiftyTwoWeekHigh') else "N/A"],
            ["Market Cap", f"${info.get('marketCap', 0):,.2f}" if info.get('marketCap') else "N/A"],
            ["Trailing P/E", info.get('trailingPE', 'N/A')],
            ["Forward P/E", info.get('forwardPE', 'N/A')],
            ["PEG Ratio", info.get('trailingPegRatio', 'N/A')],
            ["Price/Book", f"{info.get('priceToBook', 0):.2f}" if info.get('priceToBook') else "N/A"],
            ["Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A"],
            ["Short % of Float", f"{info.get('shortPercentOfFloat', 0)*100:.2f}%" if info.get('shortPercentOfFloat') else "N/A"]
        ]
        sections.extend(["\nKEY METRICS", tabulate(metrics, tablefmt="plain")])

        # Performance metrics
        performance = [
            ["Return on Equity", f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A"],
            ["Return on Assets", f"{info.get('returnOnAssets', 0)*100:.2f}%" if info.get('returnOnAssets') else "N/A"],
            ["Profit Margin", f"{info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "N/A"],
            ["Operating Margin", f"{info.get('operatingMargins', 0)*100:.2f}%" if info.get('operatingMargins') else "N/A"],
            ["Debt to Equity", f"{info.get('debtToEquity', 0):.2f}" if info.get('debtToEquity') else "N/A"],
            ["Current Ratio", f"{info.get('currentRatio', 0):.2f}" if info.get('currentRatio') else "N/A"]
        ]
        sections.extend(["\nPERFORMANCE METRICS", tabulate(performance, tablefmt="plain")])

        # Analyst coverage
        analyst = [
            ["Analyst Count", str(info.get('numberOfAnalystOpinions', 'N/A'))],
            ["Mean Target", f"${info.get('targetMeanPrice', 0):.2f}" if info.get('targetMeanPrice') else "N/A"],
            ["High Target", f"${info.get('targetHighPrice', 0):.2f}" if info.get('targetHighPrice') else "N/A"],
            ["Low Target", f"${info.get('targetLowPrice', 0):.2f}" if info.get('targetLowPrice') else "N/A"],
            ["Recommendation", info.get('recommendationKey', 'N/A').title()]
        ]
        sections.extend(["\nANALYST COVERAGE", tabulate(analyst, tablefmt="plain")])

        # Calendar dates
        if calendar := yfinance_utils.get_calendar(ticker):
            dates_data = []
            for key, value in calendar.items():
                if isinstance(value, datetime):
                    dates_data.append([key, value.strftime("%Y-%m-%d")])
                elif isinstance(value, list) and all(isinstance(d, datetime) for d in value):
                    start_date = value[0].strftime("%Y-%m-%d")
                    end_date = value[1].strftime("%Y-%m-%d")
                    dates_data.append([key, f"{start_date}-{end_date}"])

            if dates_data:
                sections.extend(["\nIMPORTANT DATES", tabulate(dates_data, headers=["Event", "Date"], tablefmt="plain")])

        # Recent recommendations
        if (recommendations := yfinance_utils.get_recommendations(ticker)) is not None and not recommendations.empty:
            rec_data = [
                [
                    row['period'],  # Use the period column directly
                    row['strongBuy'],
                    row['buy'],
                    row['hold'],
                    row['sell'],
                    row['strongSell']
                ]
                for _, row in recommendations.iterrows()
                if not all(pd.isna(val) for val in row.values)
            ]
            if rec_data:
                sections.extend(["\nRECENT ANALYST RECOMMENDATIONS",
                               tabulate(rec_data,
                                      headers=["Period", "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"],
                                      tablefmt="plain")])

        # Recent upgrades/downgrades
        if (upgrades := yfinance_utils.get_upgrades_downgrades(ticker)) is not None and not upgrades.empty:
            upg_data = [
                [
                    pd.to_datetime(row.name).strftime('%Y-%m-%d'),
                    row.get('Firm', 'N/A'),
                    f"{row.get('FromGrade', 'N/A')} → {row.get('ToGrade', 'N/A')}"
                ]
                for _, row in upgrades.iterrows()
                if not all(pd.isna(val) for val in row.values)
            ]
            if upg_data:
                sections.extend(["\nRECENT UPGRADES/DOWNGRADES",
                               tabulate(upg_data, headers=["Date", "Firm", "Change"], tablefmt="plain")])

        return "\n".join(sections)

    except Exception as e:
        logger.error(f"Error getting ticker data for {ticker}: {e}")
        return f"Failed to retrieve data for {ticker}: {str(e)}"

@mcp.tool()
def get_options(
    ticker_symbol: str,
    num_options: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
    strike_lower: float | None = None,
    strike_upper: float | None = None,
    option_type: Literal["C", "P"] | None = None,
) -> str:
    """Get options with highest open interest. Dates: YYYY-MM-DD. Type: C=calls, P=puts."""
    try:
        df, error = yfinance_utils.get_filtered_options(
            ticker_symbol, start_date, end_date, strike_lower, strike_upper, option_type
        )
        if error:
            return error

        options_data = [
            [
                "C" if "C" in row['contractSymbol'] else "P",
                f"${row['strike']:.2f}",
                row['expiryDate'],
                int(row['openInterest']) if pd.notnull(row['openInterest']) else 0,
                int(row['volume']) if pd.notnull(row['volume']) and row['volume'] > 0 else "N/A",
                f"{row['impliedVolatility']*100:.1f}%" if pd.notnull(row['impliedVolatility']) else "N/A"
            ]
            for _, row in df.head(num_options).iterrows()
        ]

        return tabulate(options_data, headers=["Type", "Strike", "Expiry", "OI", "Vol", "IV"], tablefmt="plain")

    except Exception as e:
        logger.error(f"Error getting options data for {ticker_symbol}: {e}")
        return f"Failed to retrieve options data for {ticker_symbol}: {str(e)}"

@mcp.tool()
def get_price_history(
    ticker: str,
    period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = "1mo"
) -> str:
    """Get historical price data. Shows daily data for up to 1 year, monthly aggregated data for longer periods."""
    try:
        history = yfinance_utils.get_price_history(ticker, period)
        if history is None or history.empty:
            return f"No historical data found for {ticker}. This could be due to an invalid ticker, recently delisted stock, or data provider issues."
    except YFRateLimitError:
        logger.warning(f"Rate limited while retrieving price history for {ticker}")
        return f"Yahoo Finance is currently rate limiting requests. Please try again in a few minutes. Ticker: {ticker}"
    except Exception as e:
        logger.error(f"Error retrieving price history for {ticker}: {e}")
        return f"Failed to retrieve price history for {ticker}: {str(e)}"

    short_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "ytd"]
    title_suffix = f"({period})"

    if period in short_periods:
        # Format daily data for short periods
        price_data = [
            [
                idx.strftime('%Y-%m-%d'),
                f"${row['Open']:.2f}",
                f"${row['Close']:.2f}",
                f"{row['Volume']:,.0f}",
                f"${row['Dividends']:.4f}" if row['Dividends'] > 0 else "-",
                f"{row['Stock Splits']:.0f}:1" if row['Stock Splits'] > 0 else "-"
            ]
            for idx, row in history.iterrows()
        ]
        headers = ["Date", "Open", "Close", "Volume", "Dividends", "Splits"]
        title = f"DAILY PRICE HISTORY FOR {ticker} {title_suffix}"

    else:
        # Aggregate to monthly for longer periods
        if not isinstance(history.index, pd.DatetimeIndex):
            history.index = pd.to_datetime(history.index)
        # Resample to Month Start frequency
        monthly_history = history.resample('MS').agg({
            'Open': 'first',
            'Close': 'last',
            'Volume': 'sum',
            'Dividends': 'sum',
            'Stock Splits': lambda x: x.prod() if len(x[x != 0]) > 0 else 1.0
        }).dropna(subset=['Open', 'Close'], how='all') # Drop months if all price/vol data is missing

        # Fill NaN splits with 1.0 (representing no split) AFTER aggregation
        monthly_history['Stock Splits'] = monthly_history['Stock Splits'].fillna(1.0)

        if monthly_history.empty:
             return f"No aggregated monthly data found for {ticker} for period {period}"

        price_data = [
            [
                idx.strftime('%Y-%m'),  # Format as Year-Month
                f"${row['Open']:.2f}" if pd.notnull(row['Open']) else "-",
                f"${row['Close']:.2f}" if pd.notnull(row['Close']) else "-",
                f"{row['Volume']:,.0f}" if pd.notnull(row['Volume']) and row['Volume'] > 0 else "-",
                f"${row['Dividends']:.4f}" if row['Dividends'] > 0 else "-",
                # Format split ratio if it's not 1.0 (meaning a net split occurred)
                f"{abs(row['Stock Splits']):.1f}:1" if row['Stock Splits'] != 1.0 else "-"
            ]
            for idx, row in monthly_history.iterrows()
        ]
        headers = ["Month", "Open", "Close", "Volume", "Dividends", "Splits"] # Update headers
        title = f"MONTHLY AGGREGATED PRICE HISTORY FOR {ticker} {title_suffix}"


    return title + "\n" + tabulate(price_data, headers=headers, tablefmt="plain")

@mcp.tool()
def get_financial_statements(
    ticker: str,
    statement_type: Literal["income", "balance", "cash"] = "income",
    frequency: Literal["quarterly", "annual"] = "quarterly",
) -> str:
    """Get financial statements. Types: income, balance, cash. Frequency: quarterly, annual."""
    data = yfinance_utils.get_financial_statements(ticker, statement_type, frequency)

    if data is None or data.empty:
        return f"No {statement_type} statement data found for {ticker}"

    statement_data = [
        [metric] + [
            "N/A" if pd.isna(value) else
            f"${value/1e9:.1f}B" if abs(value) >= 1e9 else
            f"${value/1e6:.1f}M"
            for value in data.loc[metric]
        ]
        for metric in data.index
    ]

    headers = ["Metric"] + [date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date) for date in data.columns]
    title = (f"{frequency.upper()} {statement_type.upper()} STATEMENT FOR {ticker}:\n"
             "(Values in billions/millions USD)")

    return title + "\n" + tabulate(statement_data, headers=headers, tablefmt="plain")

@mcp.tool()
def get_institutional_holders(ticker: str, top_n: int = 20) -> str:
    """Get major institutional and mutual fund holders."""
    inst_holders, fund_holders = yfinance_utils.get_institutional_holders(ticker, top_n)

    if (inst_holders is None or inst_holders.empty) and (fund_holders is None or fund_holders.empty):
        return f"No institutional holder data found for {ticker}"

    def format_holder_data(df: pd.DataFrame) -> list:
        return [
            [
                row['Holder'],
                f"{row['Shares']:,.0f}",
                f"${row['Value']:,.0f}",
                f"{row['pctHeld']*100:.2f}%",
                pd.to_datetime(row['Date Reported']).strftime('%Y-%m-%d') if pd.notnull(row['Date Reported']) else 'N/A',
                f"{row['pctChange']*100:+.2f}%" if pd.notnull(row['pctChange']) else "N/A"
            ]
            for _, row in df.iterrows()
        ]

    headers = ["Holder", "Shares", "Value", "% Held", "Date Reported", "% Change"]
    sections = []

    if inst_holders is not None and not inst_holders.empty:
        sections.extend(["INSTITUTIONAL HOLDERS:",
                        tabulate(format_holder_data(inst_holders), headers=headers, tablefmt="plain")])

    if fund_holders is not None and not fund_holders.empty:
        sections.extend(["\nMUTUAL FUND HOLDERS:",
                        tabulate(format_holder_data(fund_holders), headers=headers, tablefmt="plain")])

    try:
        return "\n".join(sections)
    except YFRateLimitError:
        logger.warning(f"Rate limited while retrieving institutional holders for {ticker}")
        return f"Yahoo Finance is currently rate limiting requests. Please try again in a few minutes. Ticker: {ticker}"
    except Exception as e:
        logger.error(f"Error getting institutional holders for {ticker}: {e}")
        return f"Failed to retrieve institutional holders for {ticker}: {str(e)}"

@mcp.tool()
def get_earnings_history(ticker: str) -> str:
    """Get earnings history with estimates and surprises."""
    try:
        earnings_history = yfinance_utils.get_earnings_history(ticker)

        if earnings_history is None or earnings_history.empty:
            return f"No earnings history data found for {ticker}. This could be due to an invalid ticker or data provider issues."
    except YFRateLimitError:
        logger.warning(f"Rate limited while retrieving earnings history for {ticker}")
        return f"Yahoo Finance is currently rate limiting requests. Please try again in a few minutes. Ticker: {ticker}"
    except Exception as e:
        logger.error(f"Error retrieving earnings history for {ticker}: {e}")
        return f"Failed to retrieve earnings history for {ticker}: {str(e)}"

    earnings_data = [
        [
            date.strftime('%Y-%m-%d'),
            f"${row['epsEstimate']:.2f}" if pd.notnull(row['epsEstimate']) else "N/A",
            f"${row['epsActual']:.2f}" if pd.notnull(row['epsActual']) else "N/A",
            f"${row['epsDifference']:.2f}" if pd.notnull(row['epsDifference']) else "N/A",
            f"{row['surprisePercent']:.1f}%" if pd.notnull(row['surprisePercent']) else "N/A"
        ]
        for date, row in earnings_history.iterrows()
    ]

    return (f"EARNINGS HISTORY FOR {ticker}:\n" +
            tabulate(earnings_data, headers=["Date", "EPS Est", "EPS Act", "Surprise", "Surprise %"], tablefmt="plain"))

@mcp.tool()
def get_insider_trades(ticker: str) -> str:
    """Get recent insider trading activity."""
    try:
        trades = yfinance_utils.get_insider_trades(ticker)

        if trades is None or trades.empty:
            return f"No insider trading data found for {ticker}. This could be due to an invalid ticker or data provider issues."
    except YFRateLimitError:
        logger.warning(f"Rate limited while retrieving insider trades for {ticker}")
        return f"Yahoo Finance is currently rate limiting requests. Please try again in a few minutes. Ticker: {ticker}"
    except Exception as e:
        logger.error(f"Error retrieving insider trades for {ticker}: {e}")
        return f"Failed to retrieve insider trades for {ticker}: {str(e)}"

    trades_data = [
        [
            pd.to_datetime(row['Start Date']).strftime('%Y-%m-%d') if pd.notnull(row['Start Date']) else 'N/A',
            row.get('Insider', 'N/A'),
            row.get('Position', 'N/A'),
            row.get('Transaction', 'N/A'),
            f"{row.get('Shares', 0):,.0f}",
            f"${row.get('Value', 0):,.0f}" if pd.notnull(row.get('Value')) else "N/A"
        ]
        for _, row in trades.iterrows()
    ]

    return (f"INSIDER TRADES FOR {ticker}:\n" +
            tabulate(trades_data, headers=["Date", "Insider", "Title", "Transaction", "Shares", "Value"], tablefmt="plain"))

# Only register the technical indicator tool if TA-Lib is available
if _ta_available:
    @mcp.tool()
    def calculate_technical_indicator(
        ticker: str,
        indicator: Literal["SMA", "EMA", "RSI", "MACD", "BBANDS"],
        period: Literal["1mo", "3mo", "6mo", "1y", "2y", "5y"] = "1y",
        timeperiod: int = 14,  # Default timeperiod for SMA, EMA, RSI
        fastperiod: int = 12,  # Default for MACD fast EMA
        slowperiod: int = 26,  # Default for MACD slow EMA
        signalperiod: int = 9,   # Default for MACD signal line
        nbdev: int = 2,        # Default standard deviation for BBANDS (up and down)
        matype: int = 0,       # Default MA type for BBANDS (0=SMA)
        num_results: int = 10  # Number of recent results to display
    ) -> str:
        """
        Calculates a specified technical indicator (SMA, EMA, RSI, MACD, BBANDS) for a ticker.
        Uses daily closing prices for the calculation over the specified historical `period`.
        Displays the most recent `num_results` calculated values.

        Args:
            ticker: The stock ticker symbol.
            indicator: The technical indicator to calculate.
            period: The historical data period to fetch (e.g., "1y", "2y"). Longer periods provide more context for calculation.
            timeperiod: The lookback period for SMA, EMA, RSI, and the MA within BBANDS.
            fastperiod: The fast EMA period for MACD.
            slowperiod: The slow EMA period for MACD.
            signalperiod: The signal line EMA period for MACD.
            nbdev: The number of standard deviations for the upper and lower Bollinger Bands.
            matype: The type of moving average for Bollinger Bands (0=SMA, 1=EMA, etc.). See TA-Lib docs for details.
            num_results: How many of the most recent indicator results to return.
        """

        try:
            # Fetch sufficient historical data (use the provided period, ensuring it's daily)
            history = yfinance_utils.get_price_history(ticker, period=period)
            if history is None or history.empty:
                return f"No historical data found for {ticker} for period {period}."
            if 'Close' not in history.columns:
                 return f"Historical data for {ticker} is missing the 'Close' price."

            close_prices = history['Close'].values # Use numpy array for TA-Lib

            # Ensure enough data for the calculation
            required_data_points = {
                "SMA": timeperiod,
                "EMA": timeperiod,
                "RSI": timeperiod + 1, # RSI needs one extra point
                "MACD": slowperiod + signalperiod, # Approx requirement
                "BBANDS": timeperiod # Period for the MA calculation within BBANDS
            }
            min_required = required_data_points.get(indicator, timeperiod) # Default to timeperiod if indicator not mapped
            if len(close_prices) < min_required:
                return (f"Insufficient data for {indicator} calculation ({len(close_prices)} points found, "
                        f"at least {min_required} needed for period {period}). Try a longer period.")


            indicator_result = None
            headers = ["Date", "Close"]
            indicator_output = []

            if indicator == "SMA":
                indicator_result = talib.SMA(close_prices, timeperiod=timeperiod)
                headers.append(f"SMA({timeperiod})")
            elif indicator == "EMA":
                indicator_result = talib.EMA(close_prices, timeperiod=timeperiod)
                headers.append(f"EMA({timeperiod})")
            elif indicator == "RSI":
                indicator_result = talib.RSI(close_prices, timeperiod=timeperiod)
                headers.append(f"RSI({timeperiod})")
            elif indicator == "MACD":
                # MACD returns macd, macdsignal, macdhist
                macd, macdsignal, macdhist = talib.MACD(close_prices, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
                # Combine results; ensure they are aligned with history index
                indicator_output = list(zip(macd, macdsignal, macdhist))
                headers.extend([f"MACD({fastperiod},{slowperiod})", f"Signal({signalperiod})", "Hist"])
            elif indicator == "BBANDS":
                 # BBANDS returns upperband, middleband, lowerband
                upper, middle, lower = talib.BBANDS(close_prices, timeperiod=timeperiod, nbdevup=nbdev, nbdevdn=nbdev, matype=matype)
                indicator_output = list(zip(upper, middle, lower))
                headers.extend([f"UpperBB({timeperiod},{nbdev})", f"MiddleBB({timeperiod})", f"LowerBB({timeperiod},{nbdev})"])
            else:
                return f"Indicator '{indicator}' not supported."

            # Combine results with dates and close prices, handling NaNs from TA-Lib's initial calculations
            results_table = []

            # For single output indicators
            if indicator_result is not None:
                 indicator_output = list(zip(indicator_result)) # Make it iterable like multi-output

            # Iterate backwards from the end of the data to get the most recent N valid results
            count = 0
            for i in range(len(history) - 1, -1, -1):
                if count >= num_results:
                    break

                # Check if *any* indicator value for this row is NaN
                # indicator_output contains tuples of floats/NaNs
                current_indicator_values = indicator_output[i]
                if any(pd.isna(val) for val in current_indicator_values):
                    continue # Skip rows with NaNs in the indicator results

                date_str = history.index[i].strftime('%Y-%m-%d')
                close_val = f"${history['Close'].iloc[i]:.2f}"
                formatted_indicators = [f"{val:.2f}" for val in current_indicator_values]

                results_table.append([date_str, close_val] + formatted_indicators)
                count += 1

            if not results_table:
                 return f"Could not calculate {indicator} for {ticker}. Check parameters or try a longer period."

            # Reverse the table to show oldest first (within the N results)
            results_table.reverse()

            title = f"RECENT {indicator} VALUES FOR {ticker} (Last {len(results_table)} days)"
            return title + "\n" + tabulate(results_table, headers=headers, tablefmt="plain")

        except Exception as e:
            logger.error(f"Error calculating indicator {indicator} for {ticker}: {e}")

            return f"Failed to calculate {indicator} for {ticker}: {str(e)}"

@mcp.prompt()
def investment_principles() -> str:
    """Provides a set of core investment principles and guidelines."""
    return """
Here are some core investment principles to consider:

*   Play for meaningful stakes.
*   Resist the allure of diversification. Invest in ventures that are genuinely interesting.
*   When the ship starts to sink, jump.
*   Never hesitate to abandon a venture if something more attractive comes into view.
*   Nobody knows the future.
*   Prices of stocks go up or down because of what people are feeling, thinking and doing. Not due to any easy-to-quantify measure.
*   History does *not* necessarily repeat itself. Ignore patterns on the chart.
*   Disregard what everybody says until you've thought through yourself.
*   Don't average down a bad trade.
*   Instead of attempting to organize affairs to accommodate unknowable events far in the future, react to events as they unfold in the present.
*   Every investment should be reevaluated every 3 months or so. Would you put my money into this if it were presented to you for the first time today? Is it progressing toward the ending position you envisioned?
"""

@mcp.prompt()
async def portfolio_construction_prompt() -> str:
    """Outlines a portfolio construction strategy that uses tail-hedging via married put."""
    return """
1. Analyze my current portfolio allocation, focusing on:
   - Asset classes (stocks, bonds, etc.)
   - Market exposure and correlation
   - Historical performance during normal markets and downturns
   - Current volatility and drawdown risk

2. Design a core portfolio that:
   - Maintains exposure to market growth
   - Aligns with my risk tolerance and time horizon
   - Uses low-cost index funds or ETFs where appropriate

3. Develop a tail-hedge component that:
   - Allocates ~3% of the portfolio to tail-risk protection. Example: Married put strategy, in which you buy 3-month puts with strike 15% below current price.
   - Identifies suitable put options on relevant market indices
   - Specifies strike prices, expiration dates, and position sizing
   - Estimates cost of implementation and maintenance

4. Provide a rebalancing strategy that:
   - Details when to reset hedge positions
   - Explains how to redeploy gains from successful hedges
   - Accounts for time decay of options

5. Include metrics to evaluate effectiveness:
   - Expected performance in various market scenarios
   - Impact on long-term CAGR compared to unhedged portfolio
   - Estimated reduction in volatility and maximum drawdown

6. Outline implementation steps with:
   - Specific securities or instruments to use
   - Timing considerations for establishing positions
   - Potential tax implications

Please use the tools available to you to perform your analysis and to construct the portfolio. If you're missing any information, ask the user for more details.
Explain your reasoning at each step, focusing on reducing the "volatility tax" while maintaining growth potential.
"""

# --- CNN Fear & Greed Index Resources and Tools ---

# Resource to get current Fear & Greed Index
@mcp.resource("cnn://fng/current")
async def get_current_fng() -> str:
    """Get the current CNN Fear & Greed Index as a resource."""
    logger.info("Fetching current CNN Fear & Greed Index resource")
    data = await cnn_fng_utils.fetch_fng_data()

    if not data:
        return "Error: Unable to fetch CNN Fear & Greed Index data."

    try:
        fear_and_greed = data.get("fear_and_greed", {})
        current_score = int(fear_and_greed.get("score", 0))
        current_rating = fear_and_greed.get("rating")
        timestamp = fear_and_greed.get("timestamp")

        if timestamp:
            # Convert timestamp to datetime
            dt = datetime.fromtimestamp(int(timestamp) / 1000)  # CNN API uses milliseconds
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            date_str = "Unknown date"

        # Construct output with proper formatting
        result = (
            f"CNN Fear & Greed Index (as of {date_str}):\n"
            f"Score: {current_score}\n"
            f"Rating: {current_rating}"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing CNN Fear & Greed data: {str(e)}")
        return f"Error processing CNN Fear & Greed data: {str(e)}"

# Resource to get historical Fear & Greed data
@mcp.resource("cnn://fng/history")
async def get_historical_fng() -> str:
    """Get historical CNN Fear & Greed Index data as a resource."""
    logger.info("Fetching historical CNN Fear & Greed Index resource")
    data = await cnn_fng_utils.fetch_fng_data()

    if not data:
        return "Error: Unable to fetch CNN Fear & Greed Index data."

    try:
        history = data.get("fear_and_greed_historical", [])
        if not history:
            return "No historical data available."

        # Format historical data
        lines = ["Historical CNN Fear & Greed Index:"]
        for entry in history:
            timestamp = entry.get("timestamp")
            score = entry.get("score")

            if timestamp and score:
                dt = datetime.fromtimestamp(int(timestamp) / 1000)  # CNN API uses milliseconds
                date_str = dt.strftime("%Y-%m-%d")
                classification = cnn_fng_utils.get_classification(int(score))
                lines.append(f"{date_str}: {score} ({classification})")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error processing historical Fear & Greed data: {str(e)}")
        return f"Error processing historical Fear & Greed data: {str(e)}"

# Tool to get current Fear & Greed Index
@mcp.tool()
async def get_current_fng_tool() -> str:
    """
    Get the current CNN Fear & Greed Index.

    Returns:
        str: The current Fear & Greed Index with score and rating.
    """
    logger.info("Fetching current CNN Fear & Greed Index tool")
    data = await cnn_fng_utils.fetch_fng_data()

    if not data:
        return "Error: Unable to fetch CNN Fear & Greed Index data."

    try:
        fear_and_greed = data.get("fear_and_greed", {})
        current_score = int(fear_and_greed.get("score", 0))
        current_rating = fear_and_greed.get("rating", "Unknown")
        timestamp = fear_and_greed.get("timestamp")

        if timestamp:
            dt = datetime.fromtimestamp(int(timestamp) / 1000)  # CNN API uses milliseconds
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            date_str = "Unknown date"

        # Add our own classification based on the numeric score for additional context
        score_classification = cnn_fng_utils.get_classification(current_score)

        # Construct output with proper formatting
        result = (
            f"CNN Fear & Greed Index (as of {date_str}):\n"
            f"Score: {current_score}\n"
            f"CNN Rating: {current_rating}\n"
            f"Classification: {score_classification}"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing CNN Fear & Greed data: {str(e)}")
        return f"Error processing CNN Fear & Greed data: {str(e)}"

@mcp.tool()
async def get_historical_fng_tool(days: int) -> str:
    """
    Get historical CNN Fear & Greed Index data for a specified number of days.

    Parameters:
        days (int): Number of days of historical data to retrieve (limited by the API).

    Returns:
        str: Historical Fear & Greed Index values for the specified period.
    """
    logger.info(f"Fetching historical CNN Fear & Greed Index for {days} days")

    if days <= 0:
        return "Error: Days must be a positive integer"

    data = await cnn_fng_utils.fetch_fng_data()

    if not data:
        return "Error: Unable to fetch CNN Fear & Greed Index data."

    try:
        history = data.get("fear_and_greed_historical", [])
        if not history:
            return "No historical data available."

        # Limit to the requested number of days
        # Note: The API may not provide data for every day
        limited_history = history[:min(days, len(history))]

        # Format historical data
        lines = [f"Historical CNN Fear & Greed Index (Last {len(limited_history)} days):"]
        for entry in limited_history:
            timestamp = entry.get("timestamp")
            score = entry.get("score")

            if timestamp and score:
                dt = datetime.fromtimestamp(int(timestamp) / 1000)  # CNN API uses milliseconds
                date_str = dt.strftime("%Y-%m-%d")
                score_num = int(score)
                classification = cnn_fng_utils.get_classification(score_num)
                lines.append(f"{date_str}: {score} ({classification})")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error processing historical Fear & Greed data: {str(e)}")
        return f"Error processing historical Fear & Greed data: {str(e)}"

# Tool to analyze trends in the Fear & Greed Index
@mcp.tool()
async def analyze_fng_trend(days: int) -> str:
    """
    Analyze trends in CNN Fear & Greed Index over specified days.

    Parameters:
        days (int): Number of days to analyze (limited by available data).

    Returns:
        str: A string containing the analysis results, including latest value,
             average value, trend direction, and number of data points analyzed.
    """
    logger.info(f"Analyzing CNN Fear & Greed trends over {days} days")

    if days <= 0:
        return "Error: Days must be a positive integer"

    data = await cnn_fng_utils.fetch_fng_data()

    if not data:
        return "Error: Unable to fetch CNN Fear & Greed Index data."

    try:
        # Get current data
        fear_and_greed = data.get("fear_and_greed", {})
        current_score = int(fear_and_greed.get("score", 0))
        current_rating = fear_and_greed.get("rating", "Unknown")
        current_timestamp = fear_and_greed.get("timestamp")

        # Get historical data
        history = data.get("fear_and_greed_historical", [])
        if not history:
            return "No historical data available for trend analysis."

        # Limit to the requested number of days
        limited_history = history[:min(days, len(history))]

        # Calculate statistics
        scores = [int(entry.get("score", 0)) for entry in limited_history if "score" in entry]

        if not scores:
            return "No valid scores found for trend analysis."

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        # Determine trend direction
        trend = "insufficient data to determine trend"  # Default value
        if len(scores) > 1:
            # Use the most recent 'days' points for trend calculation
            trend_scores = scores[:min(days, len(scores))]  # Use scores from the beginning (most recent) up to 'days'
            if len(trend_scores) > 1:
                # Compare first available score (most recent) with the last available score (oldest in the period)
                first_score = trend_scores[0]
                last_score = trend_scores[-1]
                diff = first_score - last_score

                if diff < -5:
                     trend = "rising significantly"
                elif diff < -2:
                     trend = "rising"
                elif diff > 5:
                     trend = "falling significantly"
                elif diff > 2:
                     trend = "falling"
                else:
                     trend = "relatively stable"

        # Format current timestamp
        if current_timestamp:
            dt = datetime.fromtimestamp(int(current_timestamp) / 1000)  # CNN API uses milliseconds
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            date_str = "Unknown date"

        # Generate the analysis report
        result = [
            f"CNN Fear & Greed Index Analysis ({len(limited_history)} days):",
            f"Latest Value: {current_score} ({current_rating}) as of {date_str}",
            f"Average Value over period: {avg_score:.1f}",
            f"Range over period: {min_score} to {max_score}",
            f"Trend over period: {trend}",
            f"Current Classification: {cnn_fng_utils.get_classification(current_score)}",
            f"Data points analyzed: {len(scores)}"
        ]

        return "\n".join(result)
    except Exception as e:
        logger.error(f"Error analyzing Fear & Greed trend: {str(e)}")
        return f"Error analyzing Fear & Greed trend: {str(e)}"