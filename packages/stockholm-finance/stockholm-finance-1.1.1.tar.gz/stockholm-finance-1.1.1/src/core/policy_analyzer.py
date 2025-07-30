"""
Government policy analysis module for Stockholm

Handles analysis of government policy news and their market impact.
"""

import numpy as np
from textblob import TextBlob

from ..config.config import POLICY_KEYWORDS


def classify_policy_impact(article):
    """
    Classify the potential market impact of a policy article.

    Enhanced to work with both legacy and new enhanced policy data formats.
    The enhanced policy fetcher already calculates impact scores, so we use
    those when available, otherwise fall back to legacy calculation.
    """
    # Check if article already has enhanced impact data from new fetcher
    if "impact_score" in article and "policy_type" in article:
        # Use enhanced data from new policy fetcher
        impact_score = article.get("impact_score", 0)

        # Classify impact level based on enhanced scoring
        if impact_score >= 2.0:
            impact_level = "High"
        elif impact_score >= 1.0:
            impact_level = "Medium"
        elif impact_score >= 0.5:
            impact_level = "Low"
        else:
            impact_level = "Minimal"

        return {
            "impact_level": impact_level,
            "impact_score": impact_score,
            "policy_type": article.get("policy_type", "General Policy"),
            "category": article.get("category", "unknown"),
            # Legacy compatibility fields
            "high_impact_keywords": int(impact_score),  # Approximate for compatibility
            "medium_impact_keywords": max(0, int(impact_score - 1)),
            "sector_impact_keywords": max(0, int(impact_score - 2)),
        }

    # Legacy calculation for backward compatibility
    text = f"{article['headline']} {article.get('text', '')}".lower()

    # Check for high impact keywords
    high_impact_score = sum(
        1 for keyword in POLICY_KEYWORDS["high_impact"] if keyword in text
    )
    medium_impact_score = sum(
        1 for keyword in POLICY_KEYWORDS["medium_impact"] if keyword in text
    )
    sector_impact_score = sum(
        1 for keyword in POLICY_KEYWORDS["sector_specific"] if keyword in text
    )

    # Calculate impact score
    impact_score = (
        high_impact_score * 3 + medium_impact_score * 2 + sector_impact_score * 1
    ) * article.get("impact_weight", 0.5)

    # Classify impact level
    if impact_score >= 3:
        impact_level = "High"
    elif impact_score >= 1.5:
        impact_level = "Medium"
    elif impact_score >= 0.5:
        impact_level = "Low"
    else:
        impact_level = "Minimal"

    return {
        "impact_level": impact_level,
        "impact_score": impact_score,
        "policy_type": "General Policy",  # Default for legacy data
        "category": article.get("category", "unknown"),
        "high_impact_keywords": high_impact_score,
        "medium_impact_keywords": medium_impact_score,
        "sector_impact_keywords": sector_impact_score,
    }


def analyze_policy_sentiment(government_articles):
    """
    Analyze sentiment of government policy news with enhanced market impact weighting.

    Now supports enhanced policy data with:
    - Multiple government agency sources (Fed, SEC, Treasury, White House, Energy)
    - Advanced impact scoring and policy type classification
    - Category-based sentiment analysis
    - Policy type breakdown (Monetary Tightening, Enforcement Action, etc.)
    """
    if not government_articles:
        return {
            "policy_sentiment": 0,
            "policy_mood": "No Policy Data",
            "high_impact_articles": [],
            "policy_categories": {},
            "policy_types": {},  # New: breakdown by policy type
            "total_policy_articles": 0,
            "enhanced_data": False,
        }

    policy_scores = []
    policy_details = []
    high_impact_articles = []
    category_sentiment = {}
    policy_type_sentiment = {}  # New: sentiment by policy type
    enhanced_data = any("policy_type" in article for article in government_articles)

    for article in government_articles:
        try:
            # Get basic sentiment
            text = f"{article['headline']} {article.get('text', '')}"
            blob = TextBlob(text)
            base_polarity = blob.sentiment.polarity

            # Get policy impact classification
            impact_info = classify_policy_impact(article)

            # Weight sentiment by impact score
            weighted_polarity = base_polarity * (1 + impact_info["impact_score"] * 0.5)

            policy_scores.append(weighted_polarity)

            article_detail = {
                "headline": article["headline"],
                "polarity": base_polarity,
                "weighted_polarity": weighted_polarity,
                "sentiment": weighted_polarity,  # Add sentiment field for tree view compatibility
                "impact_level": impact_info["impact_level"],
                "impact_score": impact_info["impact_score"],
                "category": article.get("category", "unknown"),
                "policy_type": impact_info.get("policy_type", "General Policy"),
                "source": article.get("source", ""),
                "time_ago": article.get("time_ago", ""),
                "url": article.get("url", ""),
                "text": article.get("text", ""),  # Include text for modal display
                "date": article.get("date", ""),  # Include date
            }

            policy_details.append(article_detail)

            # Track high impact articles with enhanced data
            if impact_info["impact_level"] in ["High", "Medium"]:
                # Create enhanced high impact article with additional fields
                high_impact_detail = article_detail.copy()
                high_impact_detail.update(
                    {
                        "sentiment": weighted_polarity,  # Ensure sentiment field is present
                        "summary": (
                            article.get("text", "")[:200] + "..."
                            if len(article.get("text", "")) > 200
                            else article.get("text", "")
                        ),
                    }
                )
                high_impact_articles.append(high_impact_detail)

            # Track sentiment by category
            category = article.get("category", "unknown")
            if category not in category_sentiment:
                category_sentiment[category] = []
            category_sentiment[category].append(weighted_polarity)

            # Track sentiment by policy type (enhanced data)
            policy_type = impact_info.get("policy_type", "General Policy")
            if policy_type not in policy_type_sentiment:
                policy_type_sentiment[policy_type] = []
            policy_type_sentiment[policy_type].append(weighted_polarity)

        except Exception:
            policy_scores.append(0)
            policy_details.append(
                {
                    "headline": article.get("headline", ""),
                    "polarity": 0,
                    "weighted_polarity": 0,
                    "impact_level": "Minimal",
                    "impact_score": 0,
                    "category": article.get("category", "unknown"),
                }
            )

    # Calculate overall policy sentiment
    avg_policy_sentiment = np.mean(policy_scores) if policy_scores else 0

    # Determine policy mood
    if avg_policy_sentiment > 0.15:
        policy_mood = "Market Supportive"
    elif avg_policy_sentiment > 0.05:
        policy_mood = "Mildly Supportive"
    elif avg_policy_sentiment > -0.05:
        policy_mood = "Neutral"
    elif avg_policy_sentiment > -0.15:
        policy_mood = "Cautionary"
    else:
        policy_mood = "Market Negative"

    # Calculate category averages
    category_averages = {}
    for category, scores in category_sentiment.items():
        category_averages[category] = {
            "average_sentiment": np.mean(scores),
            "article_count": len(scores),
        }

    # Calculate policy type averages (enhanced data)
    policy_type_averages = {}
    for policy_type, scores in policy_type_sentiment.items():
        policy_type_averages[policy_type] = {
            "average_sentiment": np.mean(scores),
            "article_count": len(scores),
        }

    return {
        "policy_sentiment": avg_policy_sentiment,
        "policy_mood": policy_mood,
        "high_impact_articles": sorted(
            high_impact_articles, key=lambda x: x["impact_score"], reverse=True
        )[
            :5
        ],  # Top 5 for summary display
        "articles": policy_details,  # All articles for tree view display
        "policy_categories": category_averages,
        "policy_types": policy_type_averages,  # Enhanced: breakdown by policy type
        "total_policy_articles": len(government_articles),
        "policy_details": policy_details,  # Keep for backward compatibility
        "enhanced_data": enhanced_data,  # Flag indicating if enhanced data is available
    }


def get_policy_impact_summary(policy_analysis):
    """Generate a summary of policy impact for display"""
    if not policy_analysis or policy_analysis["total_policy_articles"] == 0:
        return "No policy data available"

    policy_sentiment = policy_analysis["policy_sentiment"]
    high_impact_count = len(
        [
            a
            for a in policy_analysis["high_impact_articles"]
            if a["impact_level"] == "High"
        ]
    )
    medium_impact_count = len(
        [
            a
            for a in policy_analysis["high_impact_articles"]
            if a["impact_level"] == "Medium"
        ]
    )

    summary_parts = []

    # Sentiment assessment
    if policy_sentiment > 0.1:
        summary_parts.append("🟢 Policies are market-supportive")
    elif policy_sentiment > 0.05:
        summary_parts.append("🟡 Policies are mildly supportive")
    elif policy_sentiment > -0.05:
        summary_parts.append("⚪ Policies have neutral impact")
    elif policy_sentiment > -0.1:
        summary_parts.append("🟡 Policies create mild concerns")
    else:
        summary_parts.append("🔴 Policies create market headwinds")

    # Impact level assessment
    if high_impact_count > 0:
        summary_parts.append(
            f"⚡ {high_impact_count} high-impact announcement{'s' if high_impact_count > 1 else ''}"
        )
    if medium_impact_count > 0:
        summary_parts.append(
            f"⚠️ {medium_impact_count} medium-impact announcement{'s' if medium_impact_count > 1 else ''}"
        )

    return " | ".join(summary_parts)


def analyze_policy_categories(policy_analysis):
    """Analyze policy sentiment by category"""
    if not policy_analysis or not policy_analysis["policy_categories"]:
        return {}

    category_analysis = {}

    for category, data in policy_analysis["policy_categories"].items():
        sentiment = data["average_sentiment"]
        count = data["article_count"]

        # Determine category impact
        if sentiment > 0.1:
            impact = "Strongly Positive"
            emoji = "🟢"
        elif sentiment > 0.05:
            impact = "Positive"
            emoji = "🟢"
        elif sentiment > -0.05:
            impact = "Neutral"
            emoji = "🟡"
        elif sentiment > -0.1:
            impact = "Negative"
            emoji = "🔴"
        else:
            impact = "Strongly Negative"
            emoji = "🔴"

        category_analysis[category] = {
            "sentiment": sentiment,
            "article_count": count,
            "impact": impact,
            "emoji": emoji,
            "display_name": category.replace("_", " ").title(),
        }

    return category_analysis
