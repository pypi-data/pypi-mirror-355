"""
Sentiment analysis module for Stockholm

Handles sentiment analysis for both market news and government policy news.
"""

import re
from functools import lru_cache

import numpy as np
from textblob import TextBlob

from ..config.config import ANALYSIS_CONFIG, MAJOR_TICKERS, SECTOR_MAPPING


@lru_cache(maxsize=128)
def get_ticker_sector(ticker):
    """Map tickers to their sectors/industries - cached for performance"""
    return SECTOR_MAPPING.get(ticker, "Other")


def detect_ticker_mentions(text):
    """
    Detect all ticker mentions in the given text
    Returns a list of tickers found in the text
    """
    text_upper = text.upper()
    found_tickers = []

    for ticker in MAJOR_TICKERS:
        # Look for ticker as whole word (not part of another word)
        # Use word boundaries to avoid false positives
        pattern = r"\b" + re.escape(ticker) + r"\b"
        if re.search(pattern, text_upper):
            found_tickers.append(ticker)

    return found_tickers


def analyze_sentiment_around_ticker(text, ticker, context_window=50):
    """
    Analyze sentiment in the context around a specific ticker mention

    Args:
        text: The full article text
        ticker: The ticker to analyze sentiment for
        context_window: Number of characters before/after ticker to analyze

    Returns:
        dict with sentiment analysis for this ticker
    """
    text_upper = text.upper()
    ticker_upper = ticker.upper()

    # Find all positions where the ticker is mentioned
    pattern = r"\b" + re.escape(ticker_upper) + r"\b"
    matches = list(re.finditer(pattern, text_upper))

    if not matches:
        return {
            "ticker": ticker,
            "mentioned": False,
            "sentiment_score": 0,
            "sentiment_category": "Neutral",
            "context_snippets": [],
        }

    # Extract context around each mention and analyze sentiment
    context_snippets = []
    sentiment_scores = []

    for match in matches:
        start_pos = max(0, match.start() - context_window)
        end_pos = min(len(text), match.end() + context_window)

        # Get context from original text (preserving case)
        context = text[start_pos:end_pos].strip()
        context_snippets.append(context)

        # Analyze sentiment of this context
        try:
            blob = TextBlob(context)
            sentiment_scores.append(blob.sentiment.polarity)
        except Exception:
            sentiment_scores.append(0)

    # Calculate average sentiment across all mentions
    avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0

    # Determine sentiment category
    if avg_sentiment > 0.1:
        category = "Positive"
    elif avg_sentiment < -0.1:
        category = "Negative"
    else:
        category = "Neutral"

    return {
        "ticker": ticker,
        "mentioned": True,
        "sentiment_score": avg_sentiment,
        "sentiment_category": category,
        "context_snippets": context_snippets,
        "mention_count": len(matches),
    }


def analyze_sentiment_batch(news_data):
    """Optimized sentiment analysis"""
    sentiment_scores = []
    sentiment_details = []

    for article in news_data:
        try:
            text = f"{article['headline']} {article.get('text', '')}"
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity

            sentiment_scores.append(polarity)
            sentiment_details.append(
                {
                    "headline": article["headline"],
                    "polarity": polarity,
                    "category": (
                        "Positive"
                        if polarity > 0.1
                        else "Negative" if polarity < -0.1 else "Neutral"
                    ),
                }
            )
        except Exception:
            sentiment_scores.append(0)
            sentiment_details.append(
                {
                    "headline": article.get("headline", ""),
                    "polarity": 0,
                    "category": "Neutral",
                }
            )

    return sentiment_scores, sentiment_details


def analyze_multi_ticker_sentiment(news_data):
    """
    Enhanced sentiment analysis that detects multiple ticker mentions
    and analyzes sentiment for each ticker mentioned in each article

    Returns:
        tuple: (sentiment_scores, sentiment_details, multi_ticker_articles)
    """
    sentiment_scores = []
    sentiment_details = []
    multi_ticker_articles = []

    for i, article in enumerate(news_data):
        try:
            text = f"{article['headline']} {article.get('text', '')}"

            # Get overall sentiment (for backward compatibility)
            blob = TextBlob(text)
            overall_polarity = blob.sentiment.polarity

            # Detect all ticker mentions in the article
            mentioned_tickers = detect_ticker_mentions(text)

            # Analyze sentiment for each mentioned ticker
            ticker_sentiments = {}
            for ticker in mentioned_tickers:
                ticker_sentiment = analyze_sentiment_around_ticker(text, ticker)
                ticker_sentiments[ticker] = ticker_sentiment

            # Store overall sentiment (for backward compatibility)
            sentiment_scores.append(overall_polarity)
            sentiment_details.append(
                {
                    "headline": article["headline"],
                    "polarity": overall_polarity,
                    "category": (
                        "Positive"
                        if overall_polarity > 0.1
                        else "Negative" if overall_polarity < -0.1 else "Neutral"
                    ),
                    "mentioned_tickers": mentioned_tickers,
                    "ticker_sentiments": ticker_sentiments,
                }
            )

            # If multiple tickers mentioned, add to multi-ticker articles
            if len(mentioned_tickers) > 1:
                multi_ticker_articles.append(
                    {
                        "article_index": i,
                        "article": article,
                        "mentioned_tickers": mentioned_tickers,
                        "ticker_sentiments": ticker_sentiments,
                        "overall_sentiment": overall_polarity,
                    }
                )

        except Exception:
            sentiment_scores.append(0)
            sentiment_details.append(
                {
                    "headline": article.get("headline", ""),
                    "polarity": 0,
                    "category": "Neutral",
                    "mentioned_tickers": [],
                    "ticker_sentiments": {},
                }
            )

    return sentiment_scores, sentiment_details, multi_ticker_articles


def analyze_cross_ticker_sentiment(multi_ticker_articles):
    """
    Analyze sentiment patterns across tickers in multi-ticker articles

    Returns:
        dict: Analysis of cross-ticker sentiment patterns
    """
    if not multi_ticker_articles:
        return {
            "total_multi_ticker_articles": 0,
            "sentiment_conflicts": [],
            "ticker_pairs": {},
            "summary": "No multi-ticker articles found",
        }

    sentiment_conflicts = []
    ticker_pairs = {}

    for article_data in multi_ticker_articles:
        tickers = article_data["mentioned_tickers"]
        ticker_sentiments = article_data["ticker_sentiments"]
        article = article_data["article"]

        # Check for sentiment conflicts (one ticker positive, another negative)
        positive_tickers = []
        negative_tickers = []
        neutral_tickers = []

        for ticker in tickers:
            if ticker in ticker_sentiments:
                sentiment = ticker_sentiments[ticker]
                if sentiment["sentiment_category"] == "Positive":
                    positive_tickers.append(ticker)
                elif sentiment["sentiment_category"] == "Negative":
                    negative_tickers.append(ticker)
                else:
                    neutral_tickers.append(ticker)

        # Detect conflicts (positive and negative in same article)
        if positive_tickers and negative_tickers:
            sentiment_conflicts.append(
                {
                    "headline": article["headline"],
                    "url": article.get("url", ""),
                    "time_ago": article.get("time_ago", "Unknown"),
                    "positive_tickers": positive_tickers,
                    "negative_tickers": negative_tickers,
                    "neutral_tickers": neutral_tickers,
                    "ticker_sentiments": ticker_sentiments,
                }
            )

        # Track ticker pair co-occurrences
        for i, ticker1 in enumerate(tickers):
            for ticker2 in tickers[i + 1 :]:
                pair_key = (
                    f"{ticker1}-{ticker2}"
                    if ticker1 < ticker2
                    else f"{ticker2}-{ticker1}"
                )

                if pair_key not in ticker_pairs:
                    ticker_pairs[pair_key] = {
                        "count": 0,
                        "articles": [],
                        "sentiment_patterns": [],
                    }

                ticker_pairs[pair_key]["count"] += 1
                ticker_pairs[pair_key]["articles"].append(
                    article["headline"][:60] + "..."
                )

                # Record sentiment pattern for this pair
                sentiment1 = ticker_sentiments.get(ticker1, {}).get(
                    "sentiment_category", "Unknown"
                )
                sentiment2 = ticker_sentiments.get(ticker2, {}).get(
                    "sentiment_category", "Unknown"
                )
                ticker_pairs[pair_key]["sentiment_patterns"].append(
                    f"{ticker1}:{sentiment1}, {ticker2}:{sentiment2}"
                )

    # Sort ticker pairs by frequency
    sorted_pairs = sorted(
        ticker_pairs.items(), key=lambda x: x[1]["count"], reverse=True
    )

    return {
        "total_multi_ticker_articles": len(multi_ticker_articles),
        "sentiment_conflicts": sentiment_conflicts,
        "ticker_pairs": dict(sorted_pairs[:10]),  # Top 10 most common pairs
        "summary": f"Found {len(multi_ticker_articles)} multi-ticker articles with {len(sentiment_conflicts)} sentiment conflicts",
    }


def calculate_market_metrics(sentiment_scores, sentiment_details):
    """Calculate market sentiment metrics efficiently"""
    if not sentiment_scores:
        return {
            "market_mood": "No Data",
            "average_sentiment": 0,
            "positive_percentage": 0,
            "negative_percentage": 0,
            "neutral_percentage": 0,
            "total_articles": 0,
        }

    avg_sentiment = np.mean(sentiment_scores)
    categories = [detail["category"] for detail in sentiment_details]
    total = len(categories)

    positive_pct = (categories.count("Positive") / total) * 100
    negative_pct = (categories.count("Negative") / total) * 100
    neutral_pct = (categories.count("Neutral") / total) * 100

    # Determine market mood
    thresholds = ANALYSIS_CONFIG["sentiment_thresholds"]
    if avg_sentiment > thresholds["very_positive"]:
        market_mood = "Very Positive"
    elif avg_sentiment > thresholds["positive"]:
        market_mood = "Positive"
    elif avg_sentiment > thresholds["negative"]:
        market_mood = "Neutral"
    elif avg_sentiment > thresholds["very_negative"]:
        market_mood = "Negative"
    else:
        market_mood = "Very Negative"

    return {
        "market_mood": market_mood,
        "average_sentiment": avg_sentiment,
        "positive_percentage": positive_pct,
        "negative_percentage": negative_pct,
        "neutral_percentage": neutral_pct,
        "total_articles": total,
    }


def analyze_ticker_sentiment_optimized(news_data, sentiment_details):
    """Optimized ticker sentiment analysis"""
    ticker_sentiment = {}

    # Group articles by ticker
    ticker_articles = {}
    for i, article in enumerate(news_data):
        ticker = article.get("ticker")
        if ticker:
            if ticker not in ticker_articles:
                ticker_articles[ticker] = []
            ticker_articles[ticker].append((article, sentiment_details[i]))

    # Calculate metrics for each ticker
    for ticker, articles_with_sentiment in ticker_articles.items():
        scores = [sentiment["polarity"] for _, sentiment in articles_with_sentiment]
        categories = [sentiment["category"] for _, sentiment in articles_with_sentiment]

        total_articles = len(scores)
        positive_count = categories.count("Positive")
        negative_count = categories.count("Negative")
        neutral_count = categories.count("Neutral")

        avg_sentiment = np.mean(scores)
        sentiment_volatility = np.std(scores) if len(scores) > 1 else 0
        sentiment_consistency = 1 / (1 + sentiment_volatility)
        overall_score = avg_sentiment * sentiment_consistency

        # Find best and worst headlines with timestamps
        best_article = max(articles_with_sentiment, key=lambda x: x[1]["polarity"])[0]
        worst_article = min(articles_with_sentiment, key=lambda x: x[1]["polarity"])[0]

        ticker_sentiment[ticker] = {
            "average_sentiment": avg_sentiment,
            "sentiment_volatility": sentiment_volatility,
            "sentiment_consistency": sentiment_consistency,
            "overall_score": overall_score,
            "total_articles": total_articles,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": (positive_count / total_articles) * 100,
            "negative_percentage": (negative_count / total_articles) * 100,
            "best_headline": best_article["headline"],
            "best_headline_time": best_article.get("time_ago", "Unknown time"),
            "best_headline_datetime": best_article.get("datetime", "Unknown"),
            "best_headline_url": best_article.get("url", ""),
            "worst_headline": worst_article["headline"],
            "worst_headline_time": worst_article.get("time_ago", "Unknown time"),
            "worst_headline_datetime": worst_article.get("datetime", "Unknown"),
            "worst_headline_url": worst_article.get("url", ""),
        }

    return ticker_sentiment


def analyze_sector_sentiment_optimized(ticker_sentiment):
    """Optimized sector sentiment analysis"""
    sector_sentiment = {}

    # Group tickers by sector
    for ticker, data in ticker_sentiment.items():
        sector = get_ticker_sector(ticker)

        if sector not in sector_sentiment:
            sector_sentiment[sector] = {
                "tickers": [],
                "sentiment_scores": [],
                "total_articles": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            }

        sector_data = sector_sentiment[sector]
        sector_data["tickers"].append(
            {
                "ticker": ticker,
                "overall_score": data["overall_score"],
                "average_sentiment": data["average_sentiment"],
            }
        )

        # Aggregate counts
        sector_data["total_articles"] += data["total_articles"]
        sector_data["positive_count"] += data["positive_count"]
        sector_data["negative_count"] += data["negative_count"]
        sector_data["neutral_count"] += data["neutral_count"]
        sector_data["sentiment_scores"].append(data["average_sentiment"])

    # Calculate sector metrics
    sector_rankings = []
    for sector, data in sector_sentiment.items():
        if data["sentiment_scores"]:
            avg_sentiment = np.mean(data["sentiment_scores"])
            data["tickers"].sort(key=lambda x: x["overall_score"], reverse=True)

            # Sector strength = average of top 3 performers
            top_performers = data["tickers"][:3]
            sector_strength = np.mean([t["overall_score"] for t in top_performers])

            total_articles = data["total_articles"]
            positive_pct = (
                (data["positive_count"] / total_articles) * 100
                if total_articles > 0
                else 0
            )

            sector_rankings.append(
                {
                    "sector": sector,
                    "average_sentiment": avg_sentiment,
                    "sector_strength": sector_strength,
                    "ticker_count": len(data["tickers"]),
                    "total_articles": total_articles,
                    "positive_percentage": positive_pct,
                    "top_ticker": (
                        data["tickers"][0]["ticker"] if data["tickers"] else "N/A"
                    ),
                    "top_ticker_score": (
                        data["tickers"][0]["overall_score"] if data["tickers"] else 0
                    ),
                }
            )

    return sorted(sector_rankings, key=lambda x: x["sector_strength"], reverse=True)


def rank_tickers_optimized(ticker_sentiment):
    """Optimized ticker ranking - single sort operation"""
    ticker_infos = []

    for ticker, data in ticker_sentiment.items():
        ticker_infos.append(
            {
                "ticker": ticker,
                "average_sentiment": data["average_sentiment"],
                "overall_score": data["overall_score"],
                "total_articles": data["total_articles"],
                "positive_percentage": data["positive_percentage"],
                "negative_percentage": data["negative_percentage"],
                "best_headline": data["best_headline"],
                "best_headline_time": data["best_headline_time"],
                "best_headline_datetime": data["best_headline_datetime"],
                "best_headline_url": data["best_headline_url"],
                "worst_headline": data["worst_headline"],
                "worst_headline_time": data["worst_headline_time"],
                "worst_headline_datetime": data["worst_headline_datetime"],
                "worst_headline_url": data["worst_headline_url"],
            }
        )

    # Return only the best overall ranking (most important)
    return sorted(ticker_infos, key=lambda x: x["overall_score"], reverse=True)


def analyze_market_health_optimized(
    market_data, sentiment_analysis, policy_analysis=None
):
    """Optimized market health analysis with policy integration"""
    if not market_data:
        return {"recommendation": "INSUFFICIENT DATA", "market_trend": "Unknown"}

    price_changes = [data["price_change"] for data in market_data.values()]
    avg_market_change = np.mean(price_changes)

    # Determine market trend
    if avg_market_change > 2:
        market_trend = "Strong Bullish"
    elif avg_market_change > 0.5:
        market_trend = "Bullish"
    elif avg_market_change > -0.5:
        market_trend = "Sideways"
    elif avg_market_change > -2:
        market_trend = "Bearish"
    else:
        market_trend = "Strong Bearish"

    # Generate recommendation with policy consideration
    sentiment_score = sentiment_analysis.get("average_sentiment", 0)
    policy_score = policy_analysis.get("policy_sentiment", 0) if policy_analysis else 0

    # Combine sentiment and policy
    market_weight = ANALYSIS_CONFIG["market_weight"]
    policy_weight = ANALYSIS_CONFIG["policy_weight"]
    combined_sentiment = sentiment_score * market_weight + policy_score * policy_weight

    if combined_sentiment > 0.1 and avg_market_change > 1:
        recommendation = "STRONG BUY"
    elif combined_sentiment > 0.05 and avg_market_change > 0:
        recommendation = "BUY"
    elif combined_sentiment > -0.05 and avg_market_change > -1:
        recommendation = "HOLD"
    elif combined_sentiment > -0.1 and avg_market_change > -2:
        recommendation = "CAUTION"
    else:
        recommendation = "SELL"

    # Add policy influence note
    policy_influence = ""
    if policy_analysis and abs(policy_score) > 0.05:
        if policy_score > 0.1:
            policy_influence = " (Policy Supportive)"
        elif policy_score < -0.1:
            policy_influence = " (Policy Headwinds)"
        else:
            policy_influence = " (Policy Neutral)"

    return {
        "recommendation": recommendation + policy_influence,
        "market_trend": market_trend,
        "average_market_change": avg_market_change,
        "combined_sentiment": combined_sentiment,
        "policy_influence": policy_score,
    }
