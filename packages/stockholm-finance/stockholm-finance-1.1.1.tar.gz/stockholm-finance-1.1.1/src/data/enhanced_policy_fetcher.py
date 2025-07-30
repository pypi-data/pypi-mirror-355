"""
Enhanced Policy Data Fetcher for Stockholm

Fetches policy news from multiple government sources including:
- Federal Reserve (monetary policy)
- SEC (securities regulation)
- Treasury (fiscal policy)
- White House (executive policy)
- Department of Energy (energy policy)

Provides comprehensive policy analysis for market impact assessment.
"""

import feedparser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import pytz
from ..config.config import GOVERNMENT_RSS_FEEDS, POLICY_KEYWORDS, ANALYSIS_CONFIG
from .cache_manager import cache_manager


def fetch_enhanced_policy_feed(feed_info: Dict) -> List[Dict]:
    """
    Fetch news from a single government RSS feed with enhanced error handling.

    Args:
        feed_info: Dictionary containing feed URL, name, category, and impact weight

    Returns:
        List of article dictionaries with policy metadata
    """
    try:
        feed_url = feed_info["url"]
        feed_name = feed_info["name"]
        category = feed_info["category"]
        impact_weight = feed_info["impact_weight"]

        # Parse RSS feed with timeout
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            print(f"⚠️ No entries found for {feed_name}")
            return []

        articles = []
        cdt = pytz.timezone("America/Chicago")
        articles_per_feed = ANALYSIS_CONFIG["articles_per_feed"]

        for entry in feed.entries[:articles_per_feed]:
            try:
                headline = entry.get("title", "").strip()
                summary = entry.get("summary", "") or entry.get("description", "")
                link = entry.get("link", "")

                # Enhanced date parsing for different government feed formats
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
                    time_ago = _get_time_ago(dt_utc)
                else:
                    # Fallback to current time
                    now = datetime.now(cdt)
                    formatted_date = now.strftime("%Y-%m-%d")
                    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S CDT")
                    time_ago = "Just published"

                # Calculate policy impact score based on keywords
                impact_score = _calculate_policy_impact(headline, summary)

                articles.append(
                    {
                        "headline": headline,
                        "text": summary or headline,
                        "date": formatted_date,
                        "datetime": formatted_datetime,
                        "time_ago": time_ago,
                        "source": feed_name,
                        "category": category,
                        "impact_weight": impact_weight,
                        "impact_score": impact_score,
                        "url": link,
                        "policy_type": _classify_policy_type(
                            headline, summary, category
                        ),
                    }
                )

            except Exception as e:
                print(f"⚠️ Error parsing article from {feed_name}: {e}")
                continue

        print(f"✅ Fetched {len(articles)} articles from {feed_name}")
        return articles

    except Exception as e:
        print(f"❌ Error fetching {feed_info.get('name', 'Unknown feed')}: {e}")
        return []


def fetch_all_policy_news_parallel() -> Tuple[List[Dict], Dict]:
    """
    Fetch policy news from all government sources using parallel processing.

    Returns:
        Tuple of (articles_list, stats_dict) for analysis and monitoring
    """
    print("🏛️ Fetching policy news from government sources...")

    all_articles = []

    # Parallel processing for faster data collection
    max_workers = min(
        len(GOVERNMENT_RSS_FEEDS), 5
    )  # Limit to avoid overwhelming servers

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all feed fetching tasks
        future_to_feed = {
            executor.submit(fetch_enhanced_policy_feed, feed_info): feed_name
            for feed_name, feed_info in GOVERNMENT_RSS_FEEDS.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_feed):
            feed_name = future_to_feed[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                print(f"❌ Failed to fetch {feed_name}: {e}")

    # Generate statistics for monitoring
    stats = {
        "total_articles": len(all_articles),
        "feeds_processed": len(GOVERNMENT_RSS_FEEDS),
        "feeds_with_data": len(set(article["source"] for article in all_articles)),
        "categories": list(set(article["category"] for article in all_articles)),
        "avg_impact_score": (
            sum(article["impact_score"] for article in all_articles) / len(all_articles)
            if all_articles
            else 0
        ),
    }

    print("📊 Policy News Summary:")
    print(f"   Total Articles: {stats['total_articles']}")
    print(f"   Active Feeds: {stats['feeds_with_data']}/{stats['feeds_processed']}")
    print(f"   Categories: {', '.join(stats['categories'])}")
    print(f"   Avg Impact Score: {stats['avg_impact_score']:.2f}")

    return all_articles, stats


def cached_fetch_all_policy_news_parallel() -> Tuple[List[Dict], Dict]:
    """
    Cached version of policy news fetching with 30-minute TTL.

    This function provides intelligent caching for government policy data:
    - Cache TTL: 30 minutes (balances freshness with performance)
    - Cache Key: "policy_news_all" (single cache for all government sources)
    - Fallback: If cache fails, fetches fresh data

    Benefits:
    - Faster policy tab loading (cache hits)
    - Reduced load on government RSS servers
    - Better user experience with instant policy data
    - Automatic cache invalidation every 30 minutes

    Returns:
        Tuple of (articles_list, stats_dict) with cached or fresh data
    """

    def fetch_fresh_policy_data():
        """Fetch fresh policy data and return in cache-compatible format"""
        articles, stats = fetch_all_policy_news_parallel()
        return {"articles": articles, "stats": stats}

    # Try to get cached data first
    cache_key = "policy_news_all"
    cached_result, cache_hit = cache_manager.get_or_fetch(
        "policy_news", cache_key, fetch_fresh_policy_data
    )

    if cached_result is not None:
        articles = cached_result.get("articles", [])
        stats = cached_result.get("stats", {})

        # Add cache status to stats for monitoring
        stats["cache_hit"] = cache_hit
        stats["data_source"] = "cache" if cache_hit else "fresh"

        if cache_hit:
            print("✅ Using cached policy data (30-min TTL)")
        else:
            print("🔄 Fetched fresh policy data (cached for 30 minutes)")

        return articles, stats

    # Fallback: return empty data if everything fails
    print("⚠️ Policy data fetch failed, returning empty data")
    return [], {
        "total_articles": 0,
        "feeds_processed": len(GOVERNMENT_RSS_FEEDS),
        "feeds_with_data": 0,
        "categories": [],
        "avg_impact_score": 0,
        "cache_hit": False,
        "data_source": "fallback",
    }


def _calculate_policy_impact(headline: str, summary: str) -> float:
    """
    Calculate policy impact score based on keyword analysis.

    Args:
        headline: Article headline
        summary: Article summary/description

    Returns:
        Float impact score (0.0 to 3.0+)
    """
    text = f"{headline} {summary}".lower()
    impact_score = 0.0

    # High impact keywords (1.0 points each)
    for keyword in POLICY_KEYWORDS["high_impact"]:
        if keyword.lower() in text:
            impact_score += 1.0

    # Medium impact keywords (0.5 points each)
    for keyword in POLICY_KEYWORDS["medium_impact"]:
        if keyword.lower() in text:
            impact_score += 0.5

    # Sector specific keywords (0.3 points each)
    for keyword in POLICY_KEYWORDS["sector_specific"]:
        if keyword.lower() in text:
            impact_score += 0.3

    return round(impact_score, 2)


def _classify_policy_type(headline: str, summary: str, category: str) -> str:
    """
    Classify the type of policy based on content and source category.

    Args:
        headline: Article headline
        summary: Article summary
        category: Source category (monetary_policy, regulatory, etc.)

    Returns:
        String classification of policy type
    """
    text = f"{headline} {summary}".lower()

    # Monetary policy classification
    if category == "monetary_policy":
        if any(word in text for word in ["rate hike", "rate increase", "hawkish"]):
            return "Monetary Tightening"
        elif any(word in text for word in ["rate cut", "rate decrease", "dovish"]):
            return "Monetary Easing"
        elif "fomc" in text or "federal funds" in text:
            return "FOMC Decision"
        else:
            return "Monetary Policy"

    # Regulatory classification
    elif category == "regulatory":
        if any(word in text for word in ["enforcement", "violation", "penalty"]):
            return "Enforcement Action"
        elif any(word in text for word in ["new rule", "regulation", "requirement"]):
            return "New Regulation"
        else:
            return "Regulatory Update"

    # Fiscal policy classification
    elif category == "fiscal_policy":
        if any(word in text for word in ["spending", "budget", "stimulus"]):
            return "Fiscal Spending"
        elif any(word in text for word in ["tax", "revenue", "deficit"]):
            return "Tax Policy"
        else:
            return "Fiscal Policy"

    # Executive policy classification
    elif category == "executive_policy":
        if any(word in text for word in ["executive order", "presidential"]):
            return "Executive Order"
        elif any(word in text for word in ["trade", "tariff", "sanctions"]):
            return "Trade Policy"
        else:
            return "Executive Policy"

    # Energy policy classification
    elif category == "energy_policy":
        if any(word in text for word in ["oil", "petroleum", "crude"]):
            return "Oil Policy"
        elif any(word in text for word in ["renewable", "solar", "wind"]):
            return "Renewable Energy"
        else:
            return "Energy Policy"

    # Default classification
    return category.replace("_", " ").title()


def _get_time_ago(dt_utc: datetime) -> str:
    """
    Calculate human-readable time difference from UTC datetime.

    Args:
        dt_utc: UTC datetime object

    Returns:
        String like "2 hours ago", "1 day ago", etc.
    """
    try:
        now_utc = datetime.now(pytz.UTC)
        diff = now_utc - dt_utc

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    except Exception:
        return "Unknown time"


# Test function for development
def test_enhanced_policy_fetcher():
    """Test the enhanced policy fetcher with a single feed."""
    print("🧪 Testing Enhanced Policy Fetcher...")

    # Test with Fed press releases
    test_feed = GOVERNMENT_RSS_FEEDS["fed_press"]
    articles = fetch_enhanced_policy_feed(test_feed)

    print("\n📊 Test Results:")
    print(f"   Articles fetched: {len(articles)}")

    if articles:
        print("   Sample article:")
        sample = articles[0]
        print(f"     Headline: {sample['headline'][:60]}...")
        print(f"     Source: {sample['source']}")
        print(f"     Category: {sample['category']}")
        print(f"     Impact Score: {sample['impact_score']}")
        print(f"     Policy Type: {sample['policy_type']}")


if __name__ == "__main__":
    test_enhanced_policy_fetcher()
