#!/usr/bin/env python3
"""
🚀 Stockholm - Enhanced Interactive Dashboard

A comprehensive tool for real-time market sentiment analysis with an advanced
interactive dashboard interface powered by Textual framework.

Features:
    📊 Overview Tab         Complete market summary with real-time sentiment analysis
    🏆 Tickers Tab          Interactive sortable table with detailed ticker analysis
    📰 News Tab             Tree-organized news by sentiment with trend charts
    🏛️ Policy Tab           Government policy analysis and impact assessment

Usage:
    stockholm [options]

Options:
    --quick                 Quick analysis mode (fewer data sources, faster startup)
    --verbose               Verbose output with debug information

Navigation:
    q                       Quit application
    r                       Manual refresh data
    f                       Toggle filter controls
    1-4                     Switch between tabs
    Ctrl+E                  Export data

Examples:
    stockholm                    # Full enhanced dashboard
    stockholm --quick            # Quick mode dashboard
    stockholm --verbose          # Dashboard with debug info
"""

import argparse
import sys


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="🚀 Stockholm - Enhanced Interactive Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Dashboard Features:
  📊 Overview Tab         Complete market summary with real-time sentiment analysis
  🏆 Tickers Tab          Interactive sortable table with detailed ticker analysis
  📰 News Tab             Tree-organized news by sentiment with trend charts
  🏛️ Policy Tab           Government policy analysis and impact assessment

Navigation:
  q                       Quit application
  r                       Manual refresh data
  f                       Toggle filter controls
  1-4                     Switch between tabs
  Ctrl+E                  Export data

Examples:
  stockholm                    # Full enhanced dashboard
  stockholm --quick            # Quick mode dashboard
  stockholm --verbose          # Dashboard with debug info
  stockholm --warm-cache       # Pre-warm cache for faster startup
  stockholm --quick --warm-cache  # Quick mode with cache warming
        """,
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick analysis mode (fewer data sources, faster startup)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Verbose output with debug information"
    )
    parser.add_argument(
        "--warm-cache",
        action="store_true",
        help="Pre-warm cache before starting dashboard for faster startup",
    )

    return parser.parse_args()


def fetch_all_data(quick_mode=False):
    """Fetch all data with intelligent caching"""
    # Import cached modules for reduced API calls
    from ..data.cached_data_fetcher import (
        fetch_market_news_parallel,
        get_market_data_optimized,
    )
    from ..data.data_fetcher import (  # Keep original for RSS feeds
        fetch_government_news_parallel,
    )

    print("🚀 Fetching data with intelligent caching...")

    # Fetch market news (cached)
    news_data, news_stats = fetch_market_news_parallel(quick_mode=quick_mode)

    # Fetch government policy news (RSS feeds - less critical to cache)
    government_data, policy_stats = fetch_government_news_parallel()

    # Get market data (cached)
    market_data = get_market_data_optimized()

    # Get historical data for market indices (cached)
    from ..data.cached_data_fetcher import cached_get_market_indices_historical_data

    market_historical_data = cached_get_market_indices_historical_data()

    return (
        news_data,
        news_stats,
        government_data,
        policy_stats,
        market_data,
        market_historical_data,
    )


def analyze_all_data(
    news_data, government_data, market_data, market_historical_data=None
):
    """Analyze all data"""
    # Import analysis modules
    from ..data.cached_data_fetcher import (
        get_multiple_ticker_company_names,
        get_multiple_ticker_current_prices,
        get_multiple_ticker_prices,
    )
    from .policy_analyzer import analyze_policy_sentiment
    from .sentiment_analyzer import (
        analyze_cross_ticker_sentiment,
        analyze_market_health_optimized,
        analyze_multi_ticker_sentiment,
        analyze_sector_sentiment_optimized,
        analyze_ticker_sentiment_optimized,
        calculate_market_metrics,
        rank_tickers_optimized,
    )

    # Initialize results
    sentiment_analysis = {}
    policy_analysis = {}
    sector_rankings = []
    ticker_rankings = []
    market_health = {}
    sentiment_scores = []
    sentiment_details = []
    multi_ticker_articles = []
    cross_ticker_analysis = {}
    price_changes = {}

    # Analyze market sentiment
    if news_data:
        # Enhanced sentiment analysis with multi-ticker detection
        sentiment_scores, sentiment_details, multi_ticker_articles = (
            analyze_multi_ticker_sentiment(news_data)
        )
        sentiment_analysis = calculate_market_metrics(
            sentiment_scores, sentiment_details
        )

        # Analyze cross-ticker sentiment patterns
        cross_ticker_analysis = analyze_cross_ticker_sentiment(multi_ticker_articles)

        # Analyze ticker sentiment
        ticker_sentiment = analyze_ticker_sentiment_optimized(
            news_data, sentiment_details
        )

        # Analyze sector sentiment
        sector_rankings = analyze_sector_sentiment_optimized(ticker_sentiment)

        # Rank tickers
        ticker_rankings = rank_tickers_optimized(ticker_sentiment)

    # Analyze government policy sentiment
    if government_data:
        policy_analysis = analyze_policy_sentiment(government_data)

    # Analyze market health
    if sentiment_analysis or policy_analysis:
        market_health = analyze_market_health_optimized(
            market_data, sentiment_analysis, policy_analysis
        )

    # Get price data for ALL analyzed tickers (not just top performers)
    current_prices = {}
    company_names = {}
    if ticker_rankings:
        # Get ALL tickers that have been analyzed for sentiment
        all_analyzed_tickers = [ticker["ticker"] for ticker in ticker_rankings]

        # Fetch price changes for all analyzed tickers
        price_changes.update(get_multiple_ticker_prices(all_analyzed_tickers))

        # Fetch current prices for all analyzed tickers
        current_prices = get_multiple_ticker_current_prices(all_analyzed_tickers)

        # Fetch company names for all analyzed tickers
        company_names = get_multiple_ticker_company_names(all_analyzed_tickers)

        # Also get prices for sector performers if available
        if sector_rankings:
            sector_tickers = [sector["top_ticker"] for sector in sector_rankings[:5]]
            # Add any sector tickers that weren't already included
            additional_tickers = [
                t for t in sector_tickers if t not in all_analyzed_tickers
            ]
            if additional_tickers:
                additional_price_changes = get_multiple_ticker_prices(
                    additional_tickers
                )
                price_changes.update(additional_price_changes)
                additional_current_prices = get_multiple_ticker_current_prices(
                    additional_tickers
                )
                current_prices.update(additional_current_prices)

    return (
        sentiment_analysis,
        policy_analysis,
        market_health,
        sector_rankings,
        ticker_rankings,
        price_changes,
        current_prices,
        company_names,
        sentiment_scores,
        sentiment_details,
        multi_ticker_articles,
        cross_ticker_analysis,
        market_historical_data,
    )


def main():
    """Main function - launches the enhanced interactive dashboard"""
    args = parse_arguments()

    # Set up verbose mode if requested
    if args.verbose:
        print("🚀 STOCKHOLM - Enhanced Interactive Dashboard")
        print("=" * 70)
        print("🔧 Verbose mode enabled")
        print("⚡ Quick mode:", "ON" if args.quick else "OFF")
        print("🔥 Cache warming:", "ON" if args.warm_cache else "OFF")
        print("📊 Loading enhanced dashboard...")
        print()

    # Pre-warm cache if requested
    if args.warm_cache:
        try:
            from ..data.cache_warmer import warm_all_caches

            if args.verbose:
                print("🔥 Pre-warming cache for faster startup...")

            warm_all_caches(quick_mode=args.quick)

            if args.verbose:
                print("✅ Cache warming completed")
                print()
        except Exception as e:
            print(f"⚠️ Cache warming failed: {e}")
            print("📊 Continuing with normal startup...")
            print()

    # Launch the enhanced dashboard
    try:
        from ..ui.textual_dashboard import run_enhanced_textual_dashboard

        # Pass configuration to the dashboard
        if args.verbose:
            print("✅ Enhanced dashboard loaded successfully")
            print("🎯 Starting interactive interface...")
            print()

        run_enhanced_textual_dashboard(quick_mode=args.quick, verbose=args.verbose)

    except ImportError:
        print("❌ Textual framework not installed!")
        print("📦 Install with: pip install textual")
        print("💡 This is required for the interactive dashboard interface.")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error launching enhanced dashboard: {e}")
        if args.verbose:
            import traceback

            print("\n🔍 Detailed error information:")
            traceback.print_exc()
        print("\n💡 Try running with --verbose for more details")
        sys.exit(1)


if __name__ == "__main__":
    main()
