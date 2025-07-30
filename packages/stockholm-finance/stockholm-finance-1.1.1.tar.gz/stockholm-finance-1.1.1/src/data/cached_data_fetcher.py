#!/usr/bin/env python3
"""
Cached data fetcher - dramatically reduces API calls through intelligent caching
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Callable

import pytz
import yfinance as yf

from ..config.config import ANALYSIS_CONFIG, MAJOR_TICKERS, MARKET_INDICES
from .cache_manager import cache_manager


def cached_get_ticker_price_change(ticker: str, days: int = 1) -> float:
    """Get price change for a ticker with caching"""
    cache_key = f"{ticker}_{days}d"

    def fetch_price_change():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if len(hist) >= 2:
                if len(hist) >= days + 1:
                    old_price = hist["Close"].iloc[-(days + 1)]
                    new_price = hist["Close"].iloc[-1]
                else:
                    old_price = hist["Close"].iloc[0]
                    new_price = hist["Close"].iloc[-1]

                price_change = ((new_price / old_price) - 1) * 100
                return float(price_change)
            else:
                return 0.0
        except Exception:
            return 0.0

    result, is_cached = cache_manager.get_or_fetch(
        "prices", cache_key, fetch_price_change
    )
    return result if result is not None else 0.0


def cached_get_ticker_current_price(ticker: str) -> float:
    """Get current price for a ticker with caching"""

    def fetch_current_price():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")

            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                return float(current_price)
            else:
                return None
        except Exception:
            return None

    result, is_cached = cache_manager.get_or_fetch(
        "prices", f"{ticker}_current", fetch_current_price
    )
    return result


def cached_get_ticker_company_name(ticker: str) -> str:
    """Get company name for a ticker with long-term caching"""

    def fetch_company_name():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            company_name = (
                info.get("longName") or info.get("shortName") or info.get("displayName")
            )

            return company_name if company_name else ticker
        except Exception:
            return ticker

    result, is_cached = cache_manager.get_or_fetch(
        "company_names", ticker, fetch_company_name
    )
    return result if result is not None else ticker


def cached_get_multiple_ticker_price_data(
    tickers: List[str], days: int = 1
) -> Dict[str, Dict[str, float]]:
    """Get both current prices and price changes for multiple tickers from the same data source"""

    def batch_fetch_price_data(cache_keys_batch):
        # Extract ticker symbols from cache keys (remove the "_pricedata" suffix)
        ticker_batch = [key.replace("_pricedata", "") for key in cache_keys_batch]
        results = {}
        for ticker in ticker_batch:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(
                    period="5d"
                )  # Use 5d to ensure we have enough data

                if len(hist) >= 2:
                    # Get current price (most recent close)
                    current_price = hist["Close"].iloc[-1]

                    # Calculate price change
                    if len(hist) >= days + 1:
                        old_price = hist["Close"].iloc[-(days + 1)]
                        new_price = hist["Close"].iloc[-1]
                    else:
                        old_price = hist["Close"].iloc[0]
                        new_price = hist["Close"].iloc[-1]

                    price_change = ((new_price / old_price) - 1) * 100

                    # Map back to cache key format
                    cache_key = f"{ticker}_pricedata"
                    results[cache_key] = {
                        "current_price": float(current_price),
                        "price_change": float(price_change),
                    }
                else:
                    cache_key = f"{ticker}_pricedata"
                    results[cache_key] = {"current_price": 0.0, "price_change": 0.0}
            except Exception:
                cache_key = f"{ticker}_pricedata"
                results[cache_key] = {"current_price": 0.0, "price_change": 0.0}
        return results

    # Use cache manager's batch processing
    cache_keys = [f"{ticker}_pricedata" for ticker in tickers]
    batch_results = cache_manager.batch_get_or_fetch(
        "prices", cache_keys, batch_fetch_price_data, batch_size=5
    )

    # Map results back to ticker symbols for the calling function
    final_results = {}
    for ticker in tickers:
        cache_key = f"{ticker}_pricedata"
        final_results[ticker] = batch_results.get(
            cache_key, {"current_price": 0.0, "price_change": 0.0}
        )

    return final_results


def cached_get_multiple_ticker_prices(
    tickers: List[str], days: int = 1
) -> Dict[str, float]:
    """Get price changes for multiple tickers with intelligent batching and caching"""
    price_data = cached_get_multiple_ticker_price_data(tickers, days)
    return {ticker: data["price_change"] for ticker, data in price_data.items()}


def cached_get_multiple_ticker_current_prices(tickers: List[str]) -> Dict[str, float]:
    """Get current prices for multiple tickers with caching"""
    price_data = cached_get_multiple_ticker_price_data(tickers, days=1)
    return {ticker: data["current_price"] for ticker, data in price_data.items()}


def cached_get_multiple_ticker_company_names(tickers: List[str]) -> Dict[str, str]:
    """Get company names for multiple tickers with long-term caching"""

    def batch_fetch_company_names(ticker_batch):
        results = {}
        for ticker in ticker_batch:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                company_name = (
                    info.get("longName")
                    or info.get("shortName")
                    or info.get("displayName")
                )

                results[ticker] = company_name if company_name else ticker
            except Exception:
                results[ticker] = ticker
        return results

    return cache_manager.batch_get_or_fetch(
        "company_names", tickers, batch_fetch_company_names, batch_size=3
    )


def calculate_time_ago(pub_timestamp: float) -> str:
    """Calculate time ago string from publication timestamp"""
    try:
        cdt = pytz.timezone("America/Chicago")
        pub_datetime = datetime.fromtimestamp(pub_timestamp, tz=pytz.UTC)
        pub_datetime_cdt = pub_datetime.astimezone(cdt)

        time_diff = datetime.now(cdt) - pub_datetime_cdt

        if time_diff.days > 0:
            return f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            return f"{hours} hours ago"
        else:
            minutes = max(1, time_diff.seconds // 60)  # Show at least 1 minute
            return f"{minutes} minutes ago"
    except Exception:
        return "Unknown time"


def cached_fetch_news_for_ticker(ticker: str) -> List[Dict]:
    """Fetch news for a single ticker with caching"""

    def fetch_news():
        try:
            stock = yf.Ticker(ticker)
            news = stock.news

            if not news:
                return []

            articles = []
            articles_per_ticker = ANALYSIS_CONFIG["articles_per_ticker"]

            for article in news[:articles_per_ticker]:
                content = article.get("content", article)
                headline = content.get("title", "")
                summary = content.get("summary", "") or content.get("description", "")
                pub_date = content.get("pubDate", "")

                # Parse publication date
                pub_datetime = None
                try:
                    if isinstance(pub_date, (int, float)):
                        # Unix timestamp
                        pub_datetime = datetime.fromtimestamp(pub_date, tz=pytz.UTC)
                    elif isinstance(pub_date, str) and pub_date:
                        # Try to parse string date - Yahoo Finance uses ISO format
                        try:
                            # Handle ISO format with Z suffix (most common)
                            if pub_date.endswith("Z"):
                                pub_datetime = datetime.fromisoformat(
                                    pub_date.replace("Z", "+00:00")
                                )
                            # Handle other ISO formats
                            elif "T" in pub_date:
                                pub_datetime = datetime.fromisoformat(pub_date)
                            # Try other common formats
                            else:
                                for fmt in [
                                    "%Y-%m-%d %H:%M:%S",
                                    "%a, %d %b %Y %H:%M:%S %Z",
                                ]:
                                    try:
                                        pub_datetime = datetime.strptime(pub_date, fmt)
                                        if pub_datetime.tzinfo is None:
                                            pub_datetime = pub_datetime.replace(
                                                tzinfo=pytz.UTC
                                            )
                                        break
                                    except ValueError:
                                        continue
                        except Exception as e:
                            print(f"⚠️ Date parsing error for '{pub_date}': {e}")

                    # If we still don't have a valid datetime, use current time but mark it
                    if pub_datetime is None:
                        pub_datetime = datetime.now(pytz.UTC)
                        print(
                            f"⚠️ Using current time for article with invalid date: {pub_date}"
                        )

                except Exception as e:
                    pub_datetime = datetime.now(pytz.UTC)
                    print(f"⚠️ Date parsing exception: {e}")

                # Format dates
                cdt = pytz.timezone("America/Chicago")
                pub_datetime_cdt = pub_datetime.astimezone(cdt)
                formatted_date = pub_datetime_cdt.strftime("%Y-%m-%d")
                formatted_datetime = pub_datetime_cdt.strftime("%Y-%m-%d %H:%M:%S %Z")

                # Store the publication timestamp for later time_ago calculation
                pub_timestamp = pub_datetime.timestamp()

                if headline and len(headline) > 10:
                    articles.append(
                        {
                            "headline": headline,
                            "text": summary or headline,
                            "date": formatted_date,
                            "datetime": formatted_datetime,
                            "pub_timestamp": pub_timestamp,  # Store timestamp for dynamic time_ago calculation
                            "source": f"Yahoo Finance ({ticker})",
                            "ticker": ticker,
                            "url": content.get("canonicalUrl", {}).get("url", "")
                            or content.get("clickThroughUrl", {}).get("url", ""),
                        }
                    )

            return articles
        except Exception:
            return []

    result, _ = cache_manager.get_or_fetch("news", ticker, fetch_news)
    if result is not None:
        # Add dynamic time_ago to each article
        for article in result:
            if "pub_timestamp" in article:
                article["time_ago"] = calculate_time_ago(article["pub_timestamp"])
            else:
                article["time_ago"] = "Unknown time"
        return result
    return []


def cached_fetch_market_news_parallel(
    quick_mode: bool = False,
) -> Tuple[List[Dict], Dict]:
    """Fetch market news with intelligent caching and reduced API calls"""
    tickers = MAJOR_TICKERS[:20] if quick_mode else MAJOR_TICKERS

    print(
        f"🔍 Fetching news for {len(tickers)} tickers with caching (quick_mode: {quick_mode})"
    )

    all_articles = []
    cache_hits = 0
    api_calls = 0

    # Check cache for all tickers first
    for ticker in tickers:
        cached_articles = cache_manager.get_cached_data("news", ticker)
        if cached_articles is not None:
            all_articles.extend(cached_articles)
            cache_hits += 1
        else:
            # Only fetch if not cached
            articles = cached_fetch_news_for_ticker(ticker)
            all_articles.extend(articles)
            api_calls += 1

    print(f"📊 News cache performance: {cache_hits} hits, {api_calls} API calls")

    # Remove duplicates by headline only (not by ticker) and add dynamic time_ago
    unique_articles = []
    seen_headlines = set()

    for article in all_articles:
        # Use only headline for deduplication, not headline+ticker
        headline_key = article["headline"].lower().strip()
        if headline_key not in seen_headlines:
            seen_headlines.add(headline_key)
            # Add dynamic time_ago calculation
            article_copy = article.copy()
            if "pub_timestamp" in article_copy:
                article_copy["time_ago"] = calculate_time_ago(
                    article_copy["pub_timestamp"]
                )
            else:
                article_copy["time_ago"] = "Unknown time"
            unique_articles.append(article_copy)

    # Return articles and stats
    stats = {
        "total_articles": len(unique_articles),
        "tickers_processed": len(tickers),
        "tickers_with_news": len(set(article["ticker"] for article in unique_articles)),
        "cache_hits": cache_hits,
        "api_calls": api_calls,
    }

    print(f"🔍 Total unique articles found: {len(unique_articles)}")
    print(
        f"🔍 Tickers with news: {len(set(article['ticker'] for article in unique_articles))}"
    )

    # Use sample data if no real articles (for now)
    if not unique_articles:
        print("⚠️ No real news found, falling back to sample data")
        from data_fetcher import get_sample_data

        return get_sample_data(), stats

    return unique_articles, stats


def cached_get_market_data_optimized(days: int = None) -> Dict[str, Dict]:
    """Get market data with caching"""
    if days is None:
        days = ANALYSIS_CONFIG["market_data_days"]

    cache_key = f"market_indices_{days}d"

    def fetch_market_data():
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        market_data = {}

        for ticker, name in MARKET_INDICES.items():
            try:
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=True,
                )
                if not data.empty:
                    price_change = (
                        data["Close"].iloc[-1] / data["Close"].iloc[0] - 1
                    ) * 100
                    price_change = (
                        float(price_change.iloc[0])
                        if hasattr(price_change, "iloc")
                        else float(price_change)
                    )
                    current_price = float(data["Close"].iloc[-1])
                    market_data[ticker] = {
                        "name": name,
                        "price_change": price_change,
                        "current_price": current_price,
                    }
            except Exception as e:
                print(f"  Error fetching {ticker}: {e}")

        return market_data

    result, _ = cache_manager.get_or_fetch("market_data", cache_key, fetch_market_data)
    return result if result is not None else {}


def cached_get_market_indices_historical_data() -> Dict[str, tuple]:
    """Get 6-month historical data for market indices with caching"""
    cache_key = "market_indices_6m_historical"

    def fetch_historical_data():
        historical_data = {}

        for ticker in MARKET_INDICES.keys():
            try:
                stock = yf.Ticker(ticker)
                # Get 6 months of history
                hist = stock.history(period="6mo")

                if not hist.empty:
                    # Return list of closing prices and dates
                    prices = hist["Close"].tolist()
                    dates = hist.index.tolist()
                    historical_data[ticker] = (prices, dates)
                else:
                    historical_data[ticker] = ([], [])
            except Exception as e:
                print(f"  Error fetching historical data for {ticker}: {e}")
                historical_data[ticker] = ([], [])

        return historical_data

    result, _ = cache_manager.get_or_fetch(
        "market_data", cache_key, fetch_historical_data
    )
    return result if result is not None else {}


# Background data fetching for hot loading
class BackgroundDataFetcher:
    """Background data fetcher for continuous cache warming and hot loading"""

    def __init__(self):
        self.is_running = False
        self.fetch_thread = None
        self.update_callbacks = []

    def add_update_callback(self, callback: Callable):
        """Add a callback to be called when new data is available"""
        self.update_callbacks.append(callback)

    def start_background_fetching(self, quick_mode: bool = False):
        """Start background data fetching in a separate thread"""
        if self.is_running:
            return

        self.is_running = True
        self.fetch_thread = threading.Thread(
            target=self._background_fetch_loop, args=(quick_mode,), daemon=True
        )
        self.fetch_thread.start()

    def stop_background_fetching(self):
        """Stop background data fetching"""
        self.is_running = False
        if self.fetch_thread:
            self.fetch_thread.join(timeout=5)

    def _background_fetch_loop(self, quick_mode: bool):
        """Main background fetching loop"""
        while self.is_running:
            try:
                # Fetch price data every 2 minutes
                self._warm_price_cache(quick_mode)
                time.sleep(120)  # 2 minutes

                if not self.is_running:
                    break

                # Fetch news data every 5 minutes
                self._warm_news_cache(quick_mode)
                time.sleep(300)  # 5 minutes

                if not self.is_running:
                    break

                # Fetch market data every 10 minutes
                self._warm_market_cache()
                time.sleep(600)  # 10 minutes

                if not self.is_running:
                    break

                # Fetch policy data every 30 minutes (matches TTL)
                self._warm_policy_cache()
                time.sleep(1800)  # 30 minutes

            except Exception as e:
                print(f"⚠️ Background fetch error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def _warm_price_cache(self, quick_mode: bool):
        """Warm the price cache with fresh data"""
        try:
            tickers = MAJOR_TICKERS[:20] if quick_mode else MAJOR_TICKERS[:50]

            # Fetch prices in small batches to avoid overwhelming APIs
            batch_size = 5
            for i in range(0, len(tickers), batch_size):
                if not self.is_running:
                    break

                batch = tickers[i : i + batch_size]
                cached_get_multiple_ticker_price_data(batch)

                # Notify callbacks about new price data
                for callback in self.update_callbacks:
                    try:
                        callback("prices", batch)
                    except Exception:
                        pass

                time.sleep(1)  # Small delay between batches

        except Exception as e:
            print(f"⚠️ Price cache warming error: {e}")

    def _warm_news_cache(self, quick_mode: bool):
        """Warm the news cache with fresh data"""
        try:
            tickers = MAJOR_TICKERS[:10] if quick_mode else MAJOR_TICKERS[:30]

            # Fetch news for a subset of tickers each time
            for ticker in tickers:
                if not self.is_running:
                    break

                # Only fetch if cache is stale
                cached_data = cache_manager.get_cached_data("news", ticker)
                if cached_data is None:
                    cached_fetch_news_for_ticker(ticker)

                    # Notify callbacks about new news data
                    for callback in self.update_callbacks:
                        try:
                            callback("news", ticker)
                        except Exception:
                            pass

                time.sleep(2)  # Delay between news fetches

        except Exception as e:
            print(f"⚠️ News cache warming error: {e}")

    def _warm_market_cache(self):
        """Warm the market data cache"""
        try:
            cached_get_market_data_optimized()

            # Notify callbacks about new market data
            for callback in self.update_callbacks:
                try:
                    callback("market", "indices")
                except Exception:
                    pass

        except Exception as e:
            print(f"⚠️ Market cache warming error: {e}")

    def _warm_policy_cache(self):
        """Warm the policy cache with fresh government data"""
        try:
            from .enhanced_policy_fetcher import cached_fetch_all_policy_news_parallel

            cached_fetch_all_policy_news_parallel()

            # Notify callbacks about new policy data
            for callback in self.update_callbacks:
                try:
                    callback("policy", "government_data")
                except Exception:
                    pass

        except Exception as e:
            print(f"⚠️ Policy cache warming error: {e}")


# Global background fetcher instance
background_fetcher = BackgroundDataFetcher()


# Export cached versions to replace original functions
get_ticker_price_change = cached_get_ticker_price_change
get_ticker_current_price = cached_get_ticker_current_price
get_ticker_company_name = cached_get_ticker_company_name
get_multiple_ticker_prices = cached_get_multiple_ticker_prices
get_multiple_ticker_current_prices = cached_get_multiple_ticker_current_prices
get_multiple_ticker_company_names = cached_get_multiple_ticker_company_names
fetch_news_for_ticker = cached_fetch_news_for_ticker
fetch_market_news_parallel = cached_fetch_market_news_parallel
get_market_data_optimized = cached_get_market_data_optimized
