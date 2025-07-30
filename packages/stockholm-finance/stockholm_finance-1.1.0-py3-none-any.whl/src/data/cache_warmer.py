#!/usr/bin/env python3
"""
Cache warmer utility for Stockholm - Pre-populate cache for faster startup
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from ..config.config import MAJOR_TICKERS
from .cached_data_fetcher import (
    cached_get_multiple_ticker_company_names,
    cached_get_multiple_ticker_price_data,
    cached_get_market_data_optimized,
    cached_fetch_news_for_ticker,
)


def warm_price_cache(tickers: List[str], batch_size: int = 10) -> None:
    """Warm the price cache for given tickers"""
    print(f"🔥 Warming price cache for {len(tickers)} tickers...")

    # Process in batches to avoid overwhelming APIs
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        try:
            # Fetch price data (this will cache it)
            cached_get_multiple_ticker_price_data(batch)
            print(
                f"  ✅ Cached prices for batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}"
            )
            time.sleep(1)  # Small delay between batches
        except Exception as e:
            print(f"  ⚠️ Error caching prices for batch {i//batch_size + 1}: {e}")


def warm_company_names_cache(tickers: List[str], batch_size: int = 5) -> None:
    """Warm the company names cache for given tickers"""
    print(f"🔥 Warming company names cache for {len(tickers)} tickers...")

    # Process in smaller batches for company names (slower API)
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        try:
            # Fetch company names (this will cache them)
            cached_get_multiple_ticker_company_names(batch)
            print(
                f"  ✅ Cached names for batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}"
            )
            time.sleep(2)  # Longer delay for company names
        except Exception as e:
            print(f"  ⚠️ Error caching names for batch {i//batch_size + 1}: {e}")


def warm_news_cache(tickers: List[str], max_workers: int = 3) -> None:
    """Warm the news cache for given tickers using parallel processing"""
    print(f"🔥 Warming news cache for {len(tickers)} tickers...")

    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all news fetching tasks
        future_to_ticker = {
            executor.submit(cached_fetch_news_for_ticker, ticker): ticker
            for ticker in tickers
        }

        # Process completed tasks
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                future.result()  # This will cache the news
                completed += 1
                print(f"  ✅ Cached news for {ticker} ({completed}/{len(tickers)})")
            except Exception as e:
                completed += 1
                print(f"  ⚠️ Error caching news for {ticker}: {e}")


def warm_market_cache() -> None:
    """Warm the market data cache"""
    print("🔥 Warming market data cache...")
    try:
        cached_get_market_data_optimized()
        print("  ✅ Cached market data")
    except Exception as e:
        print(f"  ⚠️ Error caching market data: {e}")


def warm_all_caches(quick_mode: bool = False) -> None:
    """Warm all caches for faster application startup"""
    print("🚀 Starting cache warming process...")
    start_time = time.time()

    # Select tickers based on mode
    tickers = MAJOR_TICKERS[:20] if quick_mode else MAJOR_TICKERS[:50]

    try:
        # 1. Warm market data first (fastest)
        warm_market_cache()

        # 2. Warm price data (medium speed)
        warm_price_cache(tickers, batch_size=10)

        # 3. Warm company names (slower)
        warm_company_names_cache(tickers, batch_size=5)

        # 4. Warm news data (slowest, but most important)
        news_tickers = tickers[:10] if quick_mode else tickers[:30]
        warm_news_cache(news_tickers, max_workers=3)

        elapsed = time.time() - start_time
        print(f"✅ Cache warming completed in {elapsed:.1f} seconds")
        print("🚀 Stockholm should now start much faster!")

    except Exception as e:
        print(f"❌ Cache warming failed: {e}")


def main():
    """CLI entry point for cache warming"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Warm Stockholm cache for faster startup"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Quick mode - warm cache for fewer tickers"
    )

    args = parser.parse_args()
    warm_all_caches(quick_mode=args.quick)


if __name__ == "__main__":
    main()
