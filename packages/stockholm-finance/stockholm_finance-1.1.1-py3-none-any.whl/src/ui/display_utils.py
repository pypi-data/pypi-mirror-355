"""
Display utilities module for Stockholm - Simplified for detailed view only

Handles output formatting for detailed analysis view.
"""

from ..config.config import DISPLAY_CONFIG
from ..core.policy_analyzer import analyze_policy_categories
from ..core.sentiment_analyzer import get_ticker_sector


def create_hyperlink(url, text):
    """Create a clickable hyperlink for terminal output"""
    if url and url.strip():
        # ANSI escape sequence for hyperlinks: \033]8;;URL\033\\TEXT\033]8;;\033\\
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"
    else:
        return text


def print_header(title, width=70):
    """Print a formatted header with customizable width"""
    print(f"\n{title}")
    print("=" * width)


def display_market_sentiment(sentiment_analysis):
    """Display market sentiment analysis results"""
    print_header("📊 MARKET SENTIMENT ANALYSIS")
    print(
        f"  Overall Sentiment: {sentiment_analysis['market_mood']} ({sentiment_analysis['average_sentiment']:+.3f})"
    )
    print(
        f"  Positive: {sentiment_analysis['positive_percentage']:.0f}% | "
        f"Negative: {sentiment_analysis['negative_percentage']:.0f}% | "
        f"Neutral: {sentiment_analysis['neutral_percentage']:.0f}%"
    )
    print(f"  Total Articles: {sentiment_analysis['total_articles']}")


def display_policy_analysis(policy_analysis):
    """Display government policy analysis results"""
    print_header("🏛️ GOVERNMENT POLICY ANALYSIS")
    print(
        f"  Policy Sentiment: {policy_analysis['policy_mood']} ({policy_analysis['policy_sentiment']:+.3f})"
    )
    print(f"  Total Policy Articles: {policy_analysis['total_policy_articles']}")

    if policy_analysis["policy_categories"]:
        print("  Policy Categories:")
        category_analysis = analyze_policy_categories(policy_analysis)
        for _category, data in category_analysis.items():
            print(
                f"    {data['emoji']} {data['display_name']}: "
                f"{data['sentiment']:+.3f} ({data['article_count']} articles)"
            )


def display_high_impact_policy_news(policy_analysis):
    """Display high impact policy news"""
    if not policy_analysis["high_impact_articles"]:
        return

    print_header("⚡ HIGH IMPACT POLICY NEWS", 80)

    count = DISPLAY_CONFIG["high_impact_articles_count"]
    for i, article in enumerate(policy_analysis["high_impact_articles"][:count], 1):
        impact_emoji = "🔥" if article["impact_level"] == "High" else "⚠️"
        headline_link = create_hyperlink(article.get("url", ""), article["headline"])

        print(
            f"\n  {i}. {impact_emoji} {article['impact_level']} Impact - Score: {article['impact_score']:.2f}"
        )
        print(
            f"     Sentiment: {article['polarity']:+.3f} | Weighted: {article['weighted_polarity']:+.3f}"
        )
        print(f"     Source: {article.get('source', 'Unknown')}")
        print(f"     [{article.get('time_ago', 'Unknown time')}]: \"{headline_link}\"")

        if i < len(policy_analysis["high_impact_articles"][:count]):
            print("     " + "-" * DISPLAY_CONFIG["separator_length"])


def display_multi_ticker_analysis(multi_ticker_articles, cross_ticker_analysis):
    """Display multi-ticker sentiment analysis results"""
    if not multi_ticker_articles:
        return

    print("\n" + "=" * 100)
    print("🔄 MULTI-TICKER SENTIMENT ANALYSIS")
    print("=" * 100)

    print("\n📊 SUMMARY:")
    print(
        f"   • Found {len(multi_ticker_articles)} articles mentioning multiple tickers"
    )
    print(
        f"   • {len(cross_ticker_analysis['sentiment_conflicts'])} articles with conflicting sentiments"
    )
    print(
        f"   • {len(cross_ticker_analysis['ticker_pairs'])} unique ticker pairs detected"
    )

    # Show sentiment conflicts
    if cross_ticker_analysis["sentiment_conflicts"]:
        print("\n⚠️  SENTIMENT CONFLICTS:")
        print("-" * 50)

        for i, conflict in enumerate(
            cross_ticker_analysis["sentiment_conflicts"][:5], 1
        ):
            headline = (
                conflict["headline"][:70] + "..."
                if len(conflict["headline"]) > 70
                else conflict["headline"]
            )

            positive_str = ", ".join(conflict["positive_tickers"])
            negative_str = ", ".join(conflict["negative_tickers"])

            print(f"{i}. {headline}")
            print(f"   🟢 Positive for: {positive_str}")
            print(f"   🔴 Negative for: {negative_str}")
            if conflict["neutral_tickers"]:
                neutral_str = ", ".join(conflict["neutral_tickers"])
                print(f"   ⚪ Neutral for: {neutral_str}")
            print(f"   📅 {conflict['time_ago']}")
            print()

    # Show most common ticker pairs
    if cross_ticker_analysis["ticker_pairs"]:
        print("\n🔗 MOST MENTIONED TICKER PAIRS:")
        print("-" * 50)

        for i, (pair, data) in enumerate(
            list(cross_ticker_analysis["ticker_pairs"].items())[:5], 1
        ):
            print(f"{i}. {pair}: {data['count']} articles")

            # Show recent sentiment patterns
            recent_patterns = data["sentiment_patterns"][-3:]  # Last 3 patterns
            for pattern in recent_patterns:
                print(f"   • {pattern}")
            print()


def display_sector_performance(sector_rankings, price_changes):
    """Display top sector performance"""
    print_header("🏭 TOP SECTOR PERFORMANCE")

    count = DISPLAY_CONFIG["top_sectors_count"]
    for i, sector in enumerate(sector_rankings[:count], 1):
        emoji = (
            "🟢"
            if sector["average_sentiment"] > 0.1
            else "🟡" if sector["average_sentiment"] > 0 else "🔴"
        )
        top_ticker = sector["top_ticker"]
        price_change = price_changes.get(top_ticker, 0.0)
        price_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"

        print(
            f"  {i}. {emoji} {sector['sector']} - Strength: {sector['sector_strength']:.3f}"
        )
        print(
            f"     Avg Sentiment: {sector['average_sentiment']:+.3f} | "
            f"Tickers: {sector['ticker_count']} | "
            f"Positive: {sector['positive_percentage']:.0f}%"
        )
        print(
            f"     Top Performer: {top_ticker} (Score: {sector['top_ticker_score']:.3f}) "
            f"{price_emoji} {price_change:+.2f}%"
        )


def display_top_tickers(ticker_rankings, price_changes, recommendations):
    """Display top sentiment tickers"""
    print_header("🏆 TOP 5 BEST SENTIMENT TICKERS", 80)

    count = DISPLAY_CONFIG["top_tickers_count"]
    for i, ticker in enumerate(ticker_rankings[:count], 1):
        sector = get_ticker_sector(ticker["ticker"])
        ticker_symbol = ticker["ticker"]
        price_change = price_changes.get(ticker_symbol, 0.0)
        price_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"

        # Get analyst recommendation
        rec_data = recommendations.get(ticker_symbol, {})
        analyst_rec = rec_data.get("recommendation", "N/A")
        upside = rec_data.get("upside_potential", None)

        # Create recommendation display
        rec_display = f"Analyst: {analyst_rec}"
        if upside is not None:
            upside_emoji = "🎯" if upside > 10 else "📊" if upside > 0 else "⚠️"
            rec_display += f" {upside_emoji} {upside:+.1f}% upside"

        # Create clickable headline
        headline_link = create_hyperlink(
            ticker["best_headline_url"], ticker["best_headline"]
        )

        print(
            f"\n  {i}. {ticker_symbol} ({sector}) - Score: {ticker['overall_score']:.3f} "
            f"{price_emoji} {price_change:+.2f}%"
        )
        print(
            f"     Sentiment: {ticker['average_sentiment']:+.3f} | "
            f"Articles: {ticker['total_articles']} | "
            f"Positive: {ticker['positive_percentage']:.0f}%"
        )
        print(f"     {rec_display}")
        print(f"     Best News [{ticker['best_headline_time']}]: \"{headline_link}\"")
        print(f"     Published: {ticker['best_headline_datetime']}")

        # Add separator line between tickers (except for the last one)
        if i < count:
            print("     " + "-" * DISPLAY_CONFIG["separator_length"])


def display_negative_tickers(ticker_rankings, price_changes, recommendations):
    """Display tickers with negative sentiment"""
    negative_tickers = [t for t in ticker_rankings if t["average_sentiment"] < -0.05]
    if not negative_tickers:
        print("\n✅ No tickers with significantly negative sentiment found!")
        return

    print_header("⚠️ TICKERS TO WATCH (Negative Sentiment)", 80)

    count = DISPLAY_CONFIG["negative_tickers_count"]
    for i, ticker in enumerate(negative_tickers[:count], 1):
        sector = get_ticker_sector(ticker["ticker"])
        ticker_symbol = ticker["ticker"]
        price_change = price_changes.get(ticker_symbol, 0.0)
        price_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"

        # Get analyst recommendation
        rec_data = recommendations.get(ticker_symbol, {})
        analyst_rec = rec_data.get("recommendation", "N/A")
        upside = rec_data.get("upside_potential", None)

        # Create recommendation display
        rec_display = f"Analyst: {analyst_rec}"
        if upside is not None:
            upside_emoji = "🎯" if upside > 10 else "📊" if upside > 0 else "⚠️"
            rec_display += f" {upside_emoji} {upside:+.1f}% upside"

        # Create clickable headline
        headline_link = create_hyperlink(
            ticker["worst_headline_url"], ticker["worst_headline"]
        )

        print(
            f"\n  {i}. {ticker_symbol} ({sector}) - Score: {ticker['average_sentiment']:+.3f} "
            f"{price_emoji} {price_change:+.2f}%"
        )
        print(
            f"     Negative: {ticker['negative_percentage']:.0f}% | Articles: {ticker['total_articles']}"
        )
        print(f"     {rec_display}")
        print(f"     Concerning [{ticker['worst_headline_time']}]: \"{headline_link}\"")
        print(f"     Published: {ticker['worst_headline_datetime']}")

        # Add separator line between tickers (except for the last one)
        if i < len(negative_tickers[:count]):
            print("     " + "-" * DISPLAY_CONFIG["separator_length"])


def display_combined_analysis(market_health):
    """Display combined market and policy analysis"""
    print_header("🎯 COMBINED MARKET & POLICY ANALYSIS")

    combined_sentiment = market_health.get("combined_sentiment", 0)
    policy_influence = market_health.get("policy_influence", 0)

    print(f"  Combined Score: {combined_sentiment:+.3f}")
    print(f"  Policy Influence: {policy_influence:+.3f}")

    # Policy impact assessment
    if abs(policy_influence) > 0.1:
        if policy_influence > 0:
            policy_impact = (
                "🟢 Government policies are providing significant market support"
            )
        else:
            policy_impact = "🔴 Government policies are creating market headwinds"
    elif abs(policy_influence) > 0.05:
        if policy_influence > 0:
            policy_impact = "🟡 Government policies are mildly supportive"
        else:
            policy_impact = "🟡 Government policies are creating mild concerns"
    else:
        policy_impact = "⚪ Government policies have neutral market impact"

    print(f"  Policy Assessment: {policy_impact}")


def display_recommendation(market_health):
    """Display trading recommendation"""
    print_header("🚀 RECOMMENDATION")
    print(f"  {market_health['recommendation']}")
    print(
        f"  Market Trend: {market_health['market_trend']} ({market_health['average_market_change']:+.2f}%)"
    )


def display_market_indices(market_data):
    """Display market indices performance"""
    print_header("📈 MARKET INDICES PERFORMANCE")
    for index_ticker, data in market_data.items():
        emoji = "📈" if data["price_change"] > 0 else "📉"
        print(
            f"  {emoji} {data['name']} ({index_ticker}): {data['price_change']:+.2f}%"
        )


def display_sentiment_ranked_timeline(
    news_data, sentiment_scores, sentiment_details, limit=15
):
    """Display news timeline chronologically with sentiment scores"""
    print_header("🕒 RECENT NEWS TIMELINE")

    # Combine news data with sentiment scores
    combined_data = []
    for i, article in enumerate(news_data):
        if i < len(sentiment_scores) and i < len(sentiment_details):
            combined_data.append(
                {
                    "article": article,
                    "sentiment_score": sentiment_scores[i],
                    "sentiment_detail": sentiment_details[i],
                }
            )

    # Sort by recency (most recent first)
    combined_data.sort(key=lambda x: x["article"].get("datetime", ""), reverse=True)

    for i, item in enumerate(combined_data[:limit], 1):
        article = item["article"]
        sentiment_score = item["sentiment_score"]

        time_info = article.get("time_ago", "Unknown time")
        ticker = article.get("ticker", "N/A")
        headline = (
            article["headline"][:75] + "..."
            if len(article["headline"]) > 75
            else article["headline"]
        )
        headline_link = create_hyperlink(article.get("url", ""), headline)

        # Sentiment emoji and color coding (standardized thresholds)
        if sentiment_score > 0.1:
            sentiment_emoji = "🟢"
            sentiment_label = "Positive"
        elif sentiment_score < -0.1:
            sentiment_emoji = "🔴"
            sentiment_label = "Negative"
        else:
            sentiment_emoji = "🟡"
            sentiment_label = "Neutral"

        print(f'  {i}. {sentiment_emoji} [{time_info}] {ticker}: "{headline_link}"')
        print(
            f"     Sentiment: {sentiment_score:+.3f} ({sentiment_label}) | "
            f"Published: {article.get('datetime', 'Unknown')}"
        )

        # Add separator line between articles (except for the last one)
        if i < min(len(combined_data), limit):
            print()


def print_help():
    """Print comprehensive help information"""
    help_text = """
🚀 STOCKHOLM - FINANCIAL SENTIMENT ANALYSIS TOOL

DESCRIPTION:
    A comprehensive tool for analyzing market sentiment from news sources and
    government policy announcements to provide trading insights.

USAGE:
    stockholm [options]

OPTIONS:
    --help, -h              Show this help message
    --market-only           Run only market sentiment analysis
    --policy-only           Run only government policy analysis
    --sectors               Show detailed sector analysis
    --tickers               Show detailed ticker rankings
    --recommendations       Show analyst recommendations
    --indices               Show market indices performance
    --timeline              Show recent news timeline with sentiment scores (10-15 items)
    --detailed              Show traditional detailed output format (default: Textual dashboard)
    --quick                 Quick analysis (fewer sources, faster)
    --verbose               Verbose output with debug information

EXAMPLES:
    stockholm
        Run with modern Textual dashboard (default)

    stockholm --detailed
        Run with traditional detailed output

    stockholm --market-only
        Analyze only market sentiment (no government policy)

    stockholm --policy-only
        Analyze only government policy impact

    stockholm --timeline
        Show only recent news timeline with sentiment scores

    stockholm --quick
        Quick analysis with fewer data sources

    stockholm --sectors --tickers
        Show detailed sector and ticker analysis

FEATURES:
    • Real-time market sentiment analysis from multiple news sources
    • Government policy impact assessment
    • Multi-ticker sentiment analysis with conflict detection
    • Sector and individual stock performance rankings
    • Analyst recommendations integration
    • Interactive Textual dashboard with live updates
    • Comprehensive detailed analysis mode

DASHBOARD MODES:
    • Default: Modern Textual-based dashboard with real-time updates
    • Detailed: Traditional terminal output with comprehensive analysis

For more information, visit: https://github.com/yourusername/stockholm
"""
    print(help_text)
