"""
Data fetching module for Stockholm

Handles fetching news from various sources, market data, and government policy feeds.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import feedparser
import pytz
import yfinance as yf

from ..config.config import (
    ANALYSIS_CONFIG,
    MAJOR_TICKERS,
    MARKET_INDICES,
)


def get_time_ago(dt_obj):
    """Calculate how long ago an article was published"""
    try:
        # Convert to CDT timezone
        cdt = pytz.timezone("America/Chicago")
        now = datetime.now(cdt)

        # Convert article time to CDT if it has timezone info
        if dt_obj.tzinfo:
            dt_cdt = dt_obj.astimezone(cdt)
        else:
            # Assume UTC if no timezone info
            utc = pytz.UTC
            dt_utc = utc.localize(dt_obj)
            dt_cdt = dt_utc.astimezone(cdt)

        diff = now - dt_cdt

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except Exception:
        return "Unknown"


def get_ticker_price_change(ticker, days=1):
    """Get price change for a ticker over specified days"""
    try:
        stock = yf.Ticker(ticker)
        # Get recent data (last 5 days to ensure we have enough data)
        hist = stock.history(period="5d")

        if len(hist) >= 2:
            # Calculate change from days ago to most recent close
            if len(hist) >= days + 1:
                old_price = hist["Close"].iloc[-(days + 1)]
                new_price = hist["Close"].iloc[-1]
            else:
                # Fallback to available data
                old_price = hist["Close"].iloc[0]
                new_price = hist["Close"].iloc[-1]

            price_change = ((new_price / old_price) - 1) * 100
            return float(price_change)
        else:
            return 0.0
    except Exception:
        return 0.0


def get_ticker_current_price(ticker):
    """Get current price for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        # Get recent data (last 2 days to ensure we have current price)
        hist = stock.history(period="2d")

        if not hist.empty:
            current_price = hist["Close"].iloc[-1]
            return float(current_price)
        else:
            return None
    except Exception:
        return None


def get_multiple_ticker_prices(tickers, days=1):
    """Get price changes for multiple tickers efficiently"""
    price_changes = {}

    # Use parallel processing for price fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {
            executor.submit(get_ticker_price_change, ticker, days): ticker
            for ticker in tickers
        }

        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                price_change = future.result()
                price_changes[ticker] = price_change
            except Exception:
                price_changes[ticker] = 0.0

    return price_changes


def get_multiple_ticker_current_prices(tickers):
    """Get current prices for multiple tickers efficiently"""
    current_prices = {}

    # Use parallel processing for price fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {
            executor.submit(get_ticker_current_price, ticker): ticker
            for ticker in tickers
        }

        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                current_price = future.result()
                current_prices[ticker] = current_price
            except Exception:
                current_prices[ticker] = None

    return current_prices


def get_ticker_company_name(ticker):
    """Get company name for a ticker from yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Try different name fields in order of preference
        company_name = (
            info.get("longName")
            or info.get("shortName")
            or info.get("displayName")
            or info.get("quoteType", {}).get("longName")
            if isinstance(info.get("quoteType"), dict)
            else None
        )

        return company_name if company_name else ticker
    except Exception:
        return ticker


def get_multiple_ticker_company_names(tickers):
    """Get company names for multiple tickers efficiently"""
    company_names = {}

    # Use parallel processing for name fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {
            executor.submit(get_ticker_company_name, ticker): ticker
            for ticker in tickers
        }

        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                company_name = future.result()
                company_names[ticker] = company_name
            except Exception:
                company_names[ticker] = ticker

    return company_names


def get_analyst_recommendation(ticker):
    """Get analyst recommendation from yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get recommendation data
        recommendation = info.get("recommendationKey", "N/A")
        recommendation_mean = info.get("recommendationMean", None)
        target_price = info.get("targetMeanPrice", None)
        current_price = info.get("currentPrice", None) or info.get(
            "regularMarketPrice", None
        )

        # Convert recommendation key to readable format
        rec_mapping = {
            "strong_buy": "Strong Buy",
            "buy": "Buy",
            "hold": "Hold",
            "sell": "Sell",
            "strong_sell": "Strong Sell",
        }

        readable_rec = rec_mapping.get(recommendation, recommendation)

        # Calculate upside if we have target and current price
        upside = None
        if target_price and current_price and current_price > 0:
            upside = ((target_price / current_price) - 1) * 100

        return {
            "recommendation": readable_rec,
            "recommendation_mean": recommendation_mean,
            "target_price": target_price,
            "current_price": current_price,
            "upside_potential": upside,
        }
    except Exception:
        return {
            "recommendation": "N/A",
            "recommendation_mean": None,
            "target_price": None,
            "current_price": None,
            "upside_potential": None,
        }


def get_multiple_analyst_recommendations(tickers):
    """Get analyst recommendations for multiple tickers efficiently"""
    recommendations = {}

    # Use parallel processing for recommendation fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {
            executor.submit(get_analyst_recommendation, ticker): ticker
            for ticker in tickers
        }

        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                rec_data = future.result()
                recommendations[ticker] = rec_data
            except Exception:
                recommendations[ticker] = {
                    "recommendation": "N/A",
                    "recommendation_mean": None,
                    "target_price": None,
                    "current_price": None,
                    "upside_potential": None,
                }

    return recommendations


def fetch_news_for_ticker(ticker):
    """Fetch news for a single ticker - optimized for parallel processing"""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        # Debug: Print news availability for first few tickers
        if ticker in ["AAPL", "MSFT", "GOOGL"]:
            print(f"🔍 Debug: {ticker} news count: {len(news) if news else 0}")

        if not news:
            return []

        articles = []
        articles_per_ticker = ANALYSIS_CONFIG["articles_per_ticker"]

        for article in news[:articles_per_ticker]:  # Top N articles per ticker
            content = article.get("content", article)
            headline = content.get("title", "")
            summary = content.get("summary", "") or content.get("description", "")
            pub_date = content.get("pubDate", "")

            if headline and len(headline) > 10:
                # Enhanced date/time parsing with CDT timezone
                try:
                    if pub_date:
                        dt_obj = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))

                        # Convert to CDT
                        cdt = pytz.timezone("America/Chicago")
                        if dt_obj.tzinfo:
                            dt_cdt = dt_obj.astimezone(cdt)
                        else:
                            utc = pytz.UTC
                            dt_utc = utc.localize(dt_obj)
                            dt_cdt = dt_utc.astimezone(cdt)

                        formatted_date = dt_cdt.strftime("%Y-%m-%d")
                        formatted_datetime = dt_cdt.strftime("%Y-%m-%d %H:%M:%S CDT")
                        time_ago = get_time_ago(dt_obj)
                    else:
                        cdt = pytz.timezone("America/Chicago")
                        now = datetime.now(cdt)
                        formatted_date = now.strftime("%Y-%m-%d")
                        formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S CDT")
                        time_ago = "Just now"
                except Exception:
                    cdt = pytz.timezone("America/Chicago")
                    now = datetime.now(cdt)
                    formatted_date = now.strftime("%Y-%m-%d")
                    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S CDT")
                    time_ago = "Unknown"

                articles.append(
                    {
                        "headline": headline,
                        "text": summary or headline,
                        "date": formatted_date,
                        "datetime": formatted_datetime,
                        "time_ago": time_ago,
                        "source": f"Yahoo Finance ({ticker})",
                        "ticker": ticker,
                        "url": content.get("canonicalUrl", {}).get("url", "")
                        or content.get("clickThroughUrl", {}).get("url", ""),
                    }
                )

        return articles
    except Exception:
        return []


def fetch_market_news_parallel(quick_mode=False):
    """
    Fetch news using parallel processing for optimal performance.

    Performance Strategy:
    - Uses ThreadPoolExecutor to fetch news from multiple tickers simultaneously
    - Quick mode: 20 tickers for faster startup (development/testing)
    - Full mode: All ~160 tickers for comprehensive analysis (production)

    Deduplication Strategy:
    - Many tickers share the same news articles (e.g., market-wide news)
    - We deduplicate by headline to avoid sentiment double-counting
    - Case-insensitive matching to catch slight variations

    Fallback Strategy:
    - If yfinance returns no news (API issues), use sample data
    - Ensures Stockholm always has data to analyze for demonstration

    Args:
        quick_mode (bool): If True, fetch from only 20 tickers for speed

    Returns:
        tuple: (articles_list, stats_dict) for analysis and monitoring
    """
    # Ticker selection: balance between speed and comprehensiveness
    tickers = MAJOR_TICKERS[:20] if quick_mode else MAJOR_TICKERS

    print(
        f"🔍 Debug: Fetching news for {len(tickers)} tickers (quick_mode: {quick_mode})"
    )

    all_articles = []

    # Parallel processing with ThreadPoolExecutor
    # max_workers=10 balances speed vs API rate limits
    max_workers = ANALYSIS_CONFIG["max_workers"]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all ticker news fetching tasks simultaneously
        future_to_ticker = {
            executor.submit(fetch_news_for_ticker, ticker): ticker for ticker in tickers
        }

        # Collect results as they complete (not in submission order)
        for future in as_completed(future_to_ticker):
            articles = future.result()
            all_articles.extend(articles)

    # Deduplication: Remove duplicate articles by headline
    # Many tickers share the same market-wide news, so we need to deduplicate
    # to avoid skewing sentiment analysis with repeated articles
    unique_articles = []
    seen_headlines = set()

    for article in all_articles:
        # Normalize headline for comparison (lowercase, stripped)
        headline_key = article["headline"].lower().strip()
        if headline_key not in seen_headlines:
            seen_headlines.add(headline_key)
            unique_articles.append(article)

    # Generate statistics for monitoring and dashboard display
    stats = {
        "total_articles": len(unique_articles),
        "tickers_processed": len(tickers),
        "tickers_with_news": len(set(article["ticker"] for article in unique_articles)),
    }

    print(f"🔍 Debug: Total unique articles found: {len(unique_articles)}")
    print(
        f"🔍 Debug: Tickers with news: {len(set(article['ticker'] for article in unique_articles))}"
    )

    # Fallback to sample data if no real news available
    # This ensures Stockholm always has data to demonstrate functionality
    if not unique_articles:
        print("⚠️ No real news found, falling back to sample data")

    return (unique_articles if unique_articles else get_sample_data()), stats


def get_sample_data():
    """Fallback sample data if no news is available"""
    print("⚠️ No news from yfinance. Using expanded sample data...")
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S CDT")

    # Generate realistic time_ago values
    import random

    time_ago_options = [
        "2 hours ago",
        "4 hours ago",
        "6 hours ago",
        "8 hours ago",
        "12 hours ago",
        "1 day ago",
    ]

    return [
        # Technology
        {
            "headline": "Apple Inc. reports strong quarterly earnings",
            "text": "Apple beats expectations",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "AAPL",
        },
        {
            "headline": "Microsoft announces AI initiatives",
            "text": "Microsoft expands AI",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "MSFT",
        },
        {
            "headline": "Tesla delivery numbers exceed forecasts",
            "text": "Tesla strong deliveries",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "TSLA",
        },
        {
            "headline": "Amazon Web Services growth continues",
            "text": "AWS shows growth",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "AMZN",
        },
        {
            "headline": "NVIDIA benefits from AI demand",
            "text": "NVIDIA AI surge",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "NVDA",
        },
        {
            "headline": "Google announces new search features",
            "text": "Google enhances search",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "GOOGL",
        },
        {
            "headline": "Meta platforms shows user growth",
            "text": "Meta user engagement up",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "META",
        },
        {
            "headline": "Netflix content strategy pays off",
            "text": "Netflix subscriber growth",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "NFLX",
        },
        {
            "headline": "Oracle cloud services expansion",
            "text": "Oracle cloud growth",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "ORCL",
        },
        {
            "headline": "Intel chip manufacturing progress",
            "text": "Intel production ramp",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "INTC",
        },
        {
            "headline": "AMD processor market gains",
            "text": "AMD market share up",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "AMD",
        },
        # Financial
        {
            "headline": "JPMorgan Chase reports solid earnings",
            "text": "JPM strong quarter",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "JPM",
        },
        {
            "headline": "Bank of America loan growth continues",
            "text": "BAC lending up",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "BAC",
        },
        {
            "headline": "Wells Fargo operational improvements",
            "text": "WFC efficiency gains",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "WFC",
        },
        {
            "headline": "Goldman Sachs trading revenue strong",
            "text": "GS trading profits",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "GS",
        },
        {
            "headline": "Morgan Stanley wealth management growth",
            "text": "MS wealth division up",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "MS",
        },
        {
            "headline": "Citigroup international expansion",
            "text": "C global growth",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "C",
        },
        # Healthcare
        {
            "headline": "Johnson & Johnson drug pipeline progress",
            "text": "JNJ pharma development",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "JNJ",
        },
        {
            "headline": "UnitedHealth Group membership growth",
            "text": "UNH enrollment up",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "UNH",
        },
        {
            "headline": "Pfizer vaccine distribution continues",
            "text": "PFE vaccine supply",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "PFE",
        },
        # Consumer
        {
            "headline": "Walmart e-commerce strategy succeeds",
            "text": "WMT online growth",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "WMT",
        },
        {
            "headline": "Home Depot seasonal sales strong",
            "text": "HD retail performance",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "HD",
        },
        {
            "headline": "Coca-Cola global market expansion",
            "text": "KO international growth",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "KO",
        },
        {
            "headline": "Nike brand strength continues",
            "text": "NKE brand value up",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "NKE",
        },
        {
            "headline": "Disney streaming service growth",
            "text": "DIS streaming success",
            "date": current_date,
            "datetime": current_datetime,
            "time_ago": random.choice(time_ago_options),
            "source": "Sample",
            "ticker": "DIS",
        },
    ]


def get_market_data_optimized(days=None):
    """Optimized market data fetching - only store what we need"""
    if days is None:
        days = ANALYSIS_CONFIG["market_data_days"]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    market_data = {}

    for ticker, name in MARKET_INDICES.items():
        try:
            data = yf.download(
                ticker, start=start_date, end=end_date, progress=False, auto_adjust=True
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
                market_data[ticker] = {"name": name, "price_change": price_change}
        except Exception as e:
            print(f"  Error fetching {ticker}: {e}")

    return market_data


def fetch_government_rss_feed(feed_info):
    """Fetch news from a single government RSS feed"""
    try:
        feed_url = feed_info["url"]
        feed_name = feed_info["name"]
        category = feed_info["category"]
        impact_weight = feed_info["impact_weight"]

        # Parse RSS feed
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            return []

        articles = []
        cdt = pytz.timezone("America/Chicago")
        articles_per_feed = ANALYSIS_CONFIG["articles_per_feed"]

        for entry in feed.entries[:articles_per_feed]:  # Top N articles per feed
            try:
                headline = entry.get("title", "").strip()
                summary = entry.get("summary", "") or entry.get("description", "")
                link = entry.get("link", "")

                # Parse publication date
                pub_date = entry.get("published_parsed") or entry.get("updated_parsed")
                if pub_date:
                    # Convert from time.struct_time to datetime
                    dt_obj = datetime(*pub_date[:6])
                    # Assume UTC if no timezone info
                    utc = pytz.UTC
                    dt_utc = utc.localize(dt_obj)
                    dt_cdt = dt_utc.astimezone(cdt)

                    formatted_date = dt_cdt.strftime("%Y-%m-%d")
                    formatted_datetime = dt_cdt.strftime("%Y-%m-%d %H:%M:%S CDT")
                    time_ago = get_time_ago(dt_utc)
                else:
                    now = datetime.now(cdt)
                    formatted_date = now.strftime("%Y-%m-%d")
                    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S CDT")
                    time_ago = "Unknown"

                if headline and len(headline) > 10:
                    articles.append(
                        {
                            "headline": headline,
                            "text": summary or headline,
                            "date": formatted_date,
                            "datetime": formatted_datetime,
                            "time_ago": time_ago,
                            "source": feed_name,
                            "url": link,
                            "category": category,
                            "impact_weight": impact_weight,
                            "ticker": "POLICY",  # Special ticker for policy news
                        }
                    )

            except Exception:
                continue  # Skip problematic entries

        return articles

    except Exception as e:
        print(f"  Error fetching {feed_info['name']}: {e}")
        return []


def fetch_government_news_parallel():
    """
    Fetch government policy news using enhanced parallel processing with intelligent caching.

    Now includes cached data from multiple government agencies:
    - Federal Reserve (monetary policy)
    - SEC (securities regulation)
    - Treasury (fiscal policy)
    - White House (executive policy)
    - Department of Energy (energy policy)

    Features:
    - 30-minute intelligent caching for faster performance
    - Automatic cache invalidation and refresh
    - Fallback to fresh data if cache fails
    - Enhanced policy data with impact scoring and classification

    Returns enhanced policy data with impact scoring and classification.
    """
    # Import the cached enhanced policy fetcher
    from .enhanced_policy_fetcher import cached_fetch_all_policy_news_parallel

    print("🏛️ Fetching enhanced government policy data with caching...")

    # Use the cached enhanced policy fetcher for optimal performance
    all_articles, enhanced_stats = cached_fetch_all_policy_news_parallel()

    # Convert enhanced stats to match expected format for backward compatibility
    stats = {
        "total_articles": enhanced_stats.get("total_articles", 0),
        "sources_processed": enhanced_stats.get("feeds_processed", 0),
        "sources_with_news": enhanced_stats.get("feeds_with_data", 0),
        # Additional enhanced stats
        "categories": enhanced_stats.get("categories", []),
        "avg_impact_score": enhanced_stats.get("avg_impact_score", 0),
        # Cache performance stats
        "cache_hit": enhanced_stats.get("cache_hit", False),
        "data_source": enhanced_stats.get("data_source", "unknown"),
    }

    cache_status = "💾 CACHED" if stats.get("cache_hit") else "🔄 FRESH"
    print(
        f"✅ Enhanced Policy Data ({cache_status}): {stats['total_articles']} articles from {stats['sources_with_news']} sources"
    )
    print(f"📊 Categories: {', '.join(stats.get('categories', []))}")
    print(f"⚡ Avg Impact Score: {stats.get('avg_impact_score', 0):.2f}")

    return all_articles, stats
