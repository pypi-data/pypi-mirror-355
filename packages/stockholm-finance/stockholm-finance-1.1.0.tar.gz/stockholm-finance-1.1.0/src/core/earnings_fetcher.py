#!/usr/bin/env python3
"""
Earnings data fetcher for quarterly earnings tracking
"""

import warnings
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf

from ..data.cache_manager import cache_manager

# Suppress yfinance deprecation warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning, module="yfinance")


def get_ticker_quarterly_earnings(ticker: str) -> Dict[str, Any]:
    """
    Get quarterly earnings data for a ticker
    Returns comprehensive earnings metrics including revenue, net income, EPS, etc.
    """
    try:
        stock = yf.Ticker(ticker)

        # Get quarterly financials (income statement)
        quarterly_financials = stock.quarterly_financials

        if quarterly_financials is None or quarterly_financials.empty:
            return {}

        # Get basic info for current metrics
        info = stock.info

        # Extract key earnings metrics
        earnings_data = {
            "ticker": ticker,
            "last_updated": datetime.now().isoformat(),
            "quarters": [],
            "current_metrics": {},
        }

        # Current metrics from info
        current_metrics = {
            "trailing_eps": info.get("trailingEps"),
            "forward_eps": info.get("forwardEps"),
            "eps_current_year": info.get("epsCurrentYear"),
            "total_revenue": info.get("totalRevenue"),
            "revenue_per_share": info.get("revenuePerShare"),
            "earnings_growth": info.get("earningsGrowth"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
            "next_earnings_date": info.get("earningsTimestamp"),
        }
        earnings_data["current_metrics"] = current_metrics

        # Process quarterly data (last 6 quarters)
        quarters = quarterly_financials.columns[:6]  # Most recent 6 quarters

        for quarter_date in quarters:
            quarter_data = {
                "date": quarter_date.strftime("%Y-%m-%d"),
                "quarter": f"Q{((quarter_date.month - 1) // 3) + 1} {quarter_date.year}",
                "metrics": {},
            }

            # Extract key metrics for this quarter
            metrics_to_extract = {
                "Total Revenue": "revenue",
                "Net Income": "net_income",
                "Operating Income": "operating_income",
                "Cost Of Revenue": "cost_of_revenue",
                "Pretax Income": "pretax_income",
                "EBITDA": "ebitda",
                "EBIT": "ebit",
            }

            for metric_name, key in metrics_to_extract.items():
                try:
                    value = quarterly_financials.loc[metric_name, quarter_date]
                    if pd.notna(value):
                        quarter_data["metrics"][key] = float(value)
                    else:
                        quarter_data["metrics"][key] = None
                except (KeyError, IndexError):
                    quarter_data["metrics"][key] = None

            earnings_data["quarters"].append(quarter_data)

        return earnings_data

    except Exception as e:
        print(f"Error fetching earnings for {ticker}: {e}")
        return {}


def cached_get_ticker_quarterly_earnings(ticker: str) -> Dict[str, Any]:
    """Get quarterly earnings data with caching"""
    cache_key = f"earnings_{ticker}"

    def fetch_earnings():
        return get_ticker_quarterly_earnings(ticker)

    # Use earnings cache category (will use default TTL from cache manager)
    result, _ = cache_manager.get_or_fetch("earnings", cache_key, fetch_earnings)
    return result if result is not None else {}


def get_multiple_ticker_earnings(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """Get earnings data for multiple tickers efficiently"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    earnings_data = {}

    # Use parallel processing for earnings fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {
            executor.submit(cached_get_ticker_quarterly_earnings, ticker): ticker
            for ticker in tickers
        }

        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                earnings = future.result()
                earnings_data[ticker] = earnings
            except Exception as e:
                print(f"Error fetching earnings for {ticker}: {e}")
                earnings_data[ticker] = {}

    return earnings_data


def analyze_earnings_trends(earnings_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze earnings trends for a ticker
    Calculate quarter-over-quarter growth, trends, etc.
    """
    if not earnings_data or not earnings_data.get("quarters"):
        return {}

    quarters = earnings_data["quarters"]
    if len(quarters) < 2:
        return {}

    analysis = {
        "ticker": earnings_data["ticker"],
        "trends": {},
        "growth_rates": {},
        "performance": {},
    }

    # Calculate quarter-over-quarter growth rates
    for i in range(len(quarters) - 1):
        current_q = quarters[i]
        previous_q = quarters[i + 1]

        for metric in ["revenue", "net_income", "operating_income"]:
            current_val = current_q["metrics"].get(metric)
            previous_val = previous_q["metrics"].get(metric)

            if (
                current_val is not None
                and previous_val is not None
                and previous_val != 0
            ):
                growth_rate = ((current_val - previous_val) / abs(previous_val)) * 100

                if metric not in analysis["growth_rates"]:
                    analysis["growth_rates"][metric] = []

                analysis["growth_rates"][metric].append(
                    {
                        "quarter": current_q["quarter"],
                        "growth_rate": growth_rate,
                        "current_value": current_val,
                        "previous_value": previous_val,
                    }
                )

    # Calculate overall trends (improving, declining, stable)
    for metric, growth_data in analysis["growth_rates"].items():
        if len(growth_data) >= 2:
            recent_growth = [
                g["growth_rate"] for g in growth_data[:2]
            ]  # Last 2 quarters
            avg_growth = sum(recent_growth) / len(recent_growth)

            if avg_growth > 5:
                trend = "improving"
            elif avg_growth < -5:
                trend = "declining"
            else:
                trend = "stable"

            analysis["trends"][metric] = {
                "trend": trend,
                "avg_growth": avg_growth,
                "latest_growth": growth_data[0]["growth_rate"] if growth_data else 0,
            }

    # Performance assessment
    revenue_trend = analysis["trends"].get("revenue", {}).get("trend", "unknown")
    income_trend = analysis["trends"].get("net_income", {}).get("trend", "unknown")

    if revenue_trend == "improving" and income_trend == "improving":
        performance = "strong"
    elif revenue_trend == "declining" or income_trend == "declining":
        performance = "weak"
    else:
        performance = "mixed"

    analysis["performance"]["overall"] = performance
    analysis["performance"]["revenue_trend"] = revenue_trend
    analysis["performance"]["income_trend"] = income_trend

    return analysis


def get_earnings_summary_for_ticker(ticker: str) -> Dict[str, Any]:
    """Get a comprehensive earnings summary for a ticker"""
    earnings_data = cached_get_ticker_quarterly_earnings(ticker)

    if not earnings_data:
        return {"ticker": ticker, "status": "no_data"}

    trends_analysis = analyze_earnings_trends(earnings_data)

    # Combine data and analysis
    summary = {
        "ticker": ticker,
        "status": "success",
        "raw_data": earnings_data,
        "analysis": trends_analysis,
        "latest_quarter": (
            earnings_data["quarters"][0] if earnings_data["quarters"] else None
        ),
        "current_metrics": earnings_data.get("current_metrics", {}),
    }

    return summary
