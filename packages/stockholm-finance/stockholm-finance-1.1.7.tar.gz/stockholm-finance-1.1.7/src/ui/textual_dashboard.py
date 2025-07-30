#!/usr/bin/env python3
"""
Enhanced Interactive Textual Dashboard for Stockholm
Combines real-time data with advanced interactive features
"""

from datetime import datetime
from typing import Any, Dict, List

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Footer,
    Header,
    Label,
    Select,
    Static,
    Switch,
    TabbedContent,
    TabPane,
    Tree,
)
from textual_plotext import PlotextPlot


class TickerDetailModal(ModalScreen):
    """Modal screen showing detailed ticker analysis"""

    def __init__(self, ticker_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.ticker_data = ticker_data

    def compose(self) -> ComposeResult:
        ticker = self.ticker_data.get("ticker", "N/A")
        company_name = self.ticker_data.get("company_name", ticker)

        with Container(id="ticker-modal"):
            # Show both ticker and company name in title
            if company_name and company_name != ticker:
                yield Label(
                    f"📊 Detailed Analysis: {ticker} - {company_name}", id="modal-title"
                )
            else:
                yield Label(f"📊 Detailed Analysis: {ticker}", id="modal-title")

            # Create detailed table
            table = DataTable()
            table.add_columns("Metric", "Value", "Trend")

            # Add company name as first row if available
            if company_name and company_name != ticker:
                table.add_row("Company Name", company_name, "🏢")

            table.add_row(
                "Current Price", f"${self.ticker_data.get('price', 0):.2f}", "📈"
            )
            table.add_row(
                "Sentiment Score", f"{self.ticker_data.get('sentiment', 0):.3f}", "🟢"
            )
            table.add_row(
                "Article Count", str(self.ticker_data.get("articles", 0)), "📊"
            )
            table.add_row(
                "Positive %", f"{self.ticker_data.get('positive_pct', 0):.1f}%", "🟢"
            )
            table.add_row(
                "Negative %", f"{self.ticker_data.get('negative_pct', 0):.1f}%", "🔴"
            )
            table.add_row("Sector", self.ticker_data.get("sector", "N/A"), "🏭")
            yield table

            with Horizontal():
                yield Button("Close", variant="primary", id="close-modal")
                yield Button("View News", variant="success", id="view-news")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-modal":
            self.dismiss()
        elif event.button.id == "view-news":
            # Could implement news filtering for this ticker
            self.dismiss()


class FilterControls(Container):
    """Interactive filter controls"""

    def compose(self) -> ComposeResult:
        yield Label("🔍 Filters & Controls")

        with Horizontal():
            yield Select(
                [
                    ("All Sectors", "all"),
                    ("Technology", "tech"),
                    ("Financial", "finance"),
                    ("Healthcare", "health"),
                    ("Energy", "energy"),
                    ("Consumer", "consumer"),
                ],
                prompt="Select Sector",
                id="sector-filter",
            )

            yield Select(
                [
                    ("All Sentiment", "all"),
                    ("Positive Only", "positive"),
                    ("Negative Only", "negative"),
                    ("Neutral Only", "neutral"),
                ],
                prompt="Sentiment Filter",
                id="sentiment-filter",
            )

        with Horizontal():
            yield Switch(value=True, id="auto-refresh")
            yield Label("Auto-refresh")
            yield Button("🔄 Refresh Now", variant="primary", id="manual-refresh")
            yield Button("📊 Export Data", variant="success", id="export-data")


class TickerNewsTable(DataTable):
    """Interactive data table for ticker-specific news articles"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.show_cursor = True
        self.articles_data = []  # Store article data for row selection

    def on_mount(self) -> None:
        self.add_columns("#", "Headline", "Time", "Sentiment", "Score")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - store article URL for opening"""
        if event.cursor_row < len(self.articles_data):
            article_data = self.articles_data[event.cursor_row]
            article = article_data["article"]
            article_url = article.get("url", "")

            # Store the URL in the app for the open_article_url action
            if hasattr(self.app, "current_article_url"):
                self.app.current_article_url = article_url

            # Show notification with article info
            headline = article.get("headline", "No headline")[:50] + "..."
            if article_url:
                self.app.notify(
                    f"Selected: {headline} (Press 'o' to open)", severity="information"
                )
            else:
                self.app.notify(
                    f"Selected: {headline} (No URL available)", severity="warning"
                )


class ArticleTimelineChart(PlotextPlot):
    """Chart showing article publication timeline correlated with stock price - SAME as ticker info chart but focused date range"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "📈 Article Timeline with Sentiment Indicators"

    def update_chart(
        self, ticker_symbol: str, articles_data: List[Dict], price_data: Dict = None
    ):
        """Update chart using EXACT same approach as ticker info chart but with focused date range"""
        try:
            if not articles_data:
                # Clear chart if no articles
                self.plt.clear_data()
                self.plt.clear_figure()
                self.plt.text(0.5, 0.5, "No articles to display", alignment="center")
                self.plt.title(f"{ticker_symbol} - No Article Data")
                self.plt.plotsize(80, 12)
                self.refresh()
                return

            # Get article dates for determining focused range
            article_dates = []
            for article_data in articles_data:
                article = article_data["article"]
                pub_timestamp = article.get("pub_timestamp")
                if pub_timestamp:
                    try:
                        import pandas as pd

                        article_date = pd.to_datetime(pub_timestamp, unit="s")
                        article_dates.append(article_date)
                    except Exception:
                        continue

            if not article_dates:
                self.plt.clear_data()
                self.plt.clear_figure()
                self.plt.text(0.5, 0.5, "No valid article dates", alignment="center")
                self.plt.title(f"{ticker_symbol} - Invalid Date Data")
                self.plt.plotsize(80, 12)
                self.refresh()
                return

            # Get focused price data (same approach as ticker info but different date range)
            prices, dates = self._get_focused_ticker_price_history(
                ticker_symbol, article_dates
            )

            if len(prices) < 2:
                self.plt.clear_data()
                self.plt.clear_figure()
                self.plt.text(0.5, 0.5, "No price data available", alignment="center")
                self.plt.title(f"{ticker_symbol} - No Data")
                self.plt.plotsize(80, 12)
                self.refresh()
                return

            # Clear previous plot
            self.plt.clear_data()
            self.plt.clear_figure()

            # EXACT same plotting approach as ticker info chart
            chart_x_values = list(range(len(prices)))
            self.plt.plot(
                chart_x_values, prices, marker="braille", color="cyan", fillx=True
            )

            # Get article data for this ticker within the chart date range (EXACT same approach)
            article_dates_in_range, article_sentiments = (
                self._get_ticker_article_dates_focused(
                    ticker_symbol, dates, articles_data
                )
            )

            # Add article markers using EXACT same approach as ticker info chart with stacking
            if article_dates_in_range and article_sentiments:
                # Group articles by date for stacking
                articles_by_date = {}
                for article_date, sentiment in zip(
                    article_dates_in_range, article_sentiments
                ):
                    date_key = article_date.date()
                    if date_key not in articles_by_date:
                        articles_by_date[date_key] = []
                    articles_by_date[date_key].append((article_date, sentiment))

                # Plot article markers with sentiment-based colors and stacking
                for date_key, articles_on_date in articles_by_date.items():
                    x_pos = None
                    price_for_date = None

                    # Find x position and price for this date
                    for j, date in enumerate(dates):
                        if date.date() == date_key:
                            x_pos = j
                            price_for_date = prices[j]
                            break

                    if x_pos is not None and price_for_date is not None:
                        # Calculate price range for stacking with enhanced visibility
                        price_range = max(prices) - min(prices)
                        stack_offset = (
                            price_range * 0.03
                        )  # 3% of price range per stack level for better visibility

                        # Debug logging for stacking
                        if hasattr(self.app, "verbose_mode") and self.app.verbose_mode:
                            print(
                                f"🔍 STACKING DEBUG: {len(articles_on_date)} articles on {date_key}, stack_offset={stack_offset:.2f}"
                            )

                        # Sort articles by sentiment for proper layering (neutral first, then positive/negative on top)
                        # This ensures colored triangles are visible on top of neutral circles
                        def sentiment_sort_key(article):
                            sentiment = article[1]
                            if (
                                abs(sentiment) <= 0.1
                            ):  # Neutral articles first (bottom layer) - standardized threshold
                                return (0, sentiment)
                            else:  # Positive/negative articles last (top layer)
                                return (1, sentiment)

                        articles_on_date.sort(key=sentiment_sort_key)

                        for stack_index, (_, sentiment) in enumerate(articles_on_date):
                            # Calculate stacked position first
                            total_articles = len(articles_on_date)
                            center_offset = (total_articles - 1) * stack_offset / 2
                            stacked_price = (
                                price_for_date
                                + (stack_index * stack_offset)
                                - center_offset
                            )

                            # Enhanced sentiment visualization with distinct shapes and colors
                            if (
                                sentiment > 0.1
                            ):  # Positive sentiment (standardized threshold)
                                # Green triangle pointing up for positive news
                                marker_color = "green"
                                marker_symbol = "▲"
                                if (
                                    hasattr(self.app, "verbose_mode")
                                    and self.app.verbose_mode
                                ):
                                    print(
                                        f"📈 Plotting GREEN ▲ for positive sentiment: {sentiment:.3f}"
                                    )

                            elif (
                                sentiment < -0.1
                            ):  # Negative sentiment (standardized threshold)
                                # Red triangle pointing down for negative news
                                marker_color = "red"
                                marker_symbol = "▼"
                                if (
                                    hasattr(self.app, "verbose_mode")
                                    and self.app.verbose_mode
                                ):
                                    print(
                                        f"📉 Plotting RED ▼ for negative sentiment: {sentiment:.3f}"
                                    )

                            else:  # Neutral sentiment
                                # Yellow circle for neutral news
                                marker_color = "yellow"
                                marker_symbol = "●"
                                if (
                                    hasattr(self.app, "verbose_mode")
                                    and self.app.verbose_mode
                                ):
                                    print(
                                        f"⚪ Plotting YELLOW ● for neutral sentiment: {sentiment:.3f}"
                                    )

                            # Plot sentiment marker with enhanced visibility
                            try:
                                self.plt.scatter(
                                    [x_pos],
                                    [stacked_price],
                                    color=marker_color,
                                    marker=marker_symbol,
                                )
                            except Exception as e:
                                # Fallback to basic plotting if scatter fails
                                if (
                                    hasattr(self.app, "verbose_mode")
                                    and self.app.verbose_mode
                                ):
                                    print(f"⚠️ Scatter plot failed, using fallback: {e}")
                                self.plt.plot(
                                    [x_pos],
                                    [stacked_price],
                                    color=marker_color,
                                    marker=marker_symbol,
                                )

                # Create article data for influence lines (use original approach)
                article_data = list(zip(article_dates_in_range, article_sentiments))
                article_data.sort(key=lambda x: x[0])  # Sort by date

                for i, (_, _) in enumerate(article_data):
                    # Add influence section line (vertical line from this article to next)
                    if len(prices) > 0 and len(dates) > 0:  # Ensure we have data
                        if i < len(article_data) - 1:  # Not the last article
                            next_article_date = article_data[i + 1][0]
                            next_x_pos = self._get_x_position_for_date(
                                next_article_date, dates
                            )
                            if next_x_pos is not None and next_x_pos > 0:
                                # Draw vertical line at the end of this article's influence period
                                influence_x = max(
                                    0, next_x_pos - 0.5
                                )  # Slightly before next article
                                min_price = min(prices)
                                max_price = max(prices)

                                # Draw influence section line
                                try:
                                    influence_y_values = [min_price, max_price]
                                    influence_x_values = [influence_x, influence_x]
                                    self.plt.plot(
                                        influence_x_values,
                                        influence_y_values,
                                        color="gray",
                                        marker="",
                                        linestyle="--",
                                    )
                                except Exception:
                                    pass  # Skip if plotting fails
                        else:
                            # Last article - draw line to end of chart
                            if len(dates) > 1:
                                end_x = len(dates) - 1
                                min_price = min(prices)
                                max_price = max(prices)

                                # Draw final influence section line
                                try:
                                    influence_y_values = [min_price, max_price]
                                    influence_x_values = [end_x, end_x]
                                    self.plt.plot(
                                        influence_x_values,
                                        influence_y_values,
                                        color="gray",
                                        marker="",
                                        linestyle="--",
                                    )
                                except Exception:
                                    pass  # Skip if plotting fails

            # EXACT same x-axis formatting as ticker info chart
            if dates:
                date_labels = [date.strftime("%m/%d") for date in dates]
                step = max(1, len(date_labels) // 12)  # Show about 12 labels
                x_ticks = list(range(0, len(date_labels), step))
                x_labels = [date_labels[i] for i in x_ticks]
                self.plt.xticks(x_ticks, x_labels)

            # EXACT same title format as ticker info chart but with focused range info
            min_price = min(prices)
            max_price = max(prices)
            price_range = f"Range: ${min_price:.2f} - ${max_price:.2f}"
            article_count = len(article_dates_in_range) if article_dates_in_range else 0

            # Calculate focused date range for title
            start_date = min(article_dates).strftime("%m/%d")
            end_date = max(article_dates).strftime("%m/%d")
            if start_date == end_date:
                date_info = f"Focused on {start_date}"
            else:
                date_info = f"Focused {start_date}-{end_date}"

            # Enhanced title with sentiment legend
            sentiment_legend = "🟢▲ Positive | 🔴▼ Negative | 🟡● Neutral"
            self.plt.title(
                f"{ticker_symbol} - {date_info} | {price_range} | {article_count} Articles\n{sentiment_legend}"
            )

            # EXACT same styling as ticker info chart
            self.plt.xlabel("Date")
            self.plt.ylabel("Price ($)")
            self.plt.grid(True, True)
            self.plt.plotsize(80, 12)  # Same size as ticker info chart

            self.refresh()

        except Exception as e:
            # Fallback display
            self.plt.clear_data()
            self.plt.clear_figure()
            self.plt.text(
                0.5, 0.5, f"Chart error: {str(e)[:30]}...", alignment="center"
            )
            self.plt.title(f"{ticker_symbol} - Chart Error")
            self.plt.plotsize(80, 12)
            self.refresh()

    def _get_price_data_for_range(self, ticker_symbol: str, article_dates: List):
        """Get stock price data covering the article date range (legacy method)"""
        try:
            import yfinance as yf
            import pandas as pd

            if not article_dates:
                return [], []

            # Determine date range (add buffer around article dates)
            start_date = min(article_dates) - pd.Timedelta(days=7)
            end_date = max(article_dates) + pd.Timedelta(days=7)

            # Fetch stock data
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(start=start_date, end=end_date)

            if not hist.empty:
                prices = hist["Close"].tolist()
                dates = hist.index.tolist()
                return prices, dates
            else:
                return [], []

        except Exception:
            return [], []

    def _get_focused_ticker_price_history(
        self, ticker_symbol: str, article_dates: List
    ):
        """Get focused price history using only trading days"""
        try:
            import yfinance as yf
            import pandas as pd

            if not article_dates:
                return [], []

            # Calculate focused date range based on article dates
            min_article_date = min(article_dates)
            max_article_date = max(article_dates)

            # Determine buffer based on article date span
            article_span_days = (max_article_date - min_article_date).days

            if article_span_days == 0:
                buffer_days = 7  # Same day articles - show 7 days around
            elif article_span_days <= 3:
                buffer_days = 10  # Articles within 3 days - show 10 days buffer
            elif article_span_days <= 7:
                buffer_days = 14  # Articles within a week - show 14 days buffer
            else:
                buffer_days = 21  # Articles span more than a week - show 21 days buffer

            # Create date range for fetching trading data
            start_date = min_article_date - pd.Timedelta(days=buffer_days)
            end_date = max_article_date + pd.Timedelta(days=buffer_days)

            # Get trading data - this will only include trading days
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(start=start_date, end=end_date + pd.Timedelta(days=10))

            if not hist.empty:
                # Return EXACT same format as ticker info chart
                prices = hist["Close"].tolist()
                dates = hist.index.tolist()
                return prices, dates
            else:
                return [], []

        except Exception:
            return [], []

    def _get_ticker_article_dates_focused(
        self, ticker_symbol: str, chart_dates_range: List, articles_data: List[Dict]
    ):
        """Get article dates using EXACT same approach as ticker info chart"""
        try:
            import pandas as pd

            # Use EXACT same approach as working ticker info chart
            # Get news data from app cache (same as _get_ticker_article_dates)
            if not hasattr(self.app, "data_cache") or not self.app.data_cache:
                return [], []

            news_data = self.app.data_cache.get("news_data", [])
            sentiment_details = self.app.data_cache.get("sentiment_details", [])

            if not news_data or not sentiment_details:
                return [], []

            # Get the date range for filtering
            if not chart_dates_range:
                return [], []

            start_date = chart_dates_range[0]
            end_date = chart_dates_range[-1]

            article_dates = []
            article_sentiments = []

            # Filter articles that mention this ticker and are within date range (EXACT same logic)
            total_articles_checked = 0
            articles_mentioning_ticker = 0
            articles_with_valid_dates = 0
            articles_mapped_successfully = 0

            for i, article in enumerate(news_data):
                total_articles_checked += 1
                if i >= len(sentiment_details):
                    continue

                # Check if ticker is mentioned using the pre-computed mentioned_tickers list
                mentioned_tickers = sentiment_details[i].get("mentioned_tickers", [])
                if ticker_symbol not in mentioned_tickers:
                    continue

                articles_mentioning_ticker += 1

                # Get publication timestamp
                pub_timestamp = article.get("pub_timestamp")
                if pub_timestamp:
                    articles_with_valid_dates += 1
                    try:
                        # EXACT same date conversion as ticker info chart
                        article_date = pd.to_datetime(
                            pub_timestamp, unit="s"
                        ).tz_localize("UTC")

                        # Convert to same timezone as chart dates if needed
                        if hasattr(start_date, "tz") and start_date.tz:
                            article_date = article_date.tz_convert(start_date.tz)
                        else:
                            article_date = article_date.tz_localize(None)

                        # Map article to nearest trading day if it falls on non-trading day
                        mapped_date = self._map_to_nearest_trading_day(
                            article_date, chart_dates_range
                        )

                        # Check if mapped date is within chart date range
                        if mapped_date and start_date <= mapped_date <= end_date:
                            article_dates.append(mapped_date)
                            articles_mapped_successfully += 1

                            # Get sentiment for this ticker from sentiment_details
                            sentiment_detail = sentiment_details[i]
                            ticker_sentiments = sentiment_detail.get(
                                "ticker_sentiments", {}
                            )
                            sentiment_score = ticker_sentiments.get(
                                ticker_symbol, {}
                            ).get("polarity", 0)
                            article_sentiments.append(sentiment_score)

                    except Exception:
                        continue

            return article_dates, article_sentiments

        except Exception:
            return [], []

    def _map_to_nearest_trading_day(self, article_date, chart_dates_range):
        """
        Map article published on non-trading day to the nearest (last) trading day.

        This is necessary because:
        1. Articles can be published on weekends/holidays when markets are closed
        2. Stock price charts only contain trading days (Mon-Fri, excluding holidays)
        3. We need to map weekend articles to the last available trading day for visualization

        Algorithm:
        - Normalize dates to remove time components for accurate comparison
        - Search backwards through trading days to find the last one <= article date
        - If article is from before all trading data, use the earliest trading day

        Args:
            article_date: When the article was published (can be any day)
            chart_dates_range: List of available trading days from price data

        Returns:
            datetime: The nearest trading day for chart positioning
        """
        try:
            if not chart_dates_range:
                return article_date  # Fallback to original date

            import pandas as pd

            # Convert article date to normalized date for comparison (removes time component)
            # This ensures we're comparing dates only, not datetime with time
            if hasattr(article_date, "normalize"):
                article_date_norm = article_date.normalize()
            else:
                article_date_norm = pd.Timestamp(article_date).normalize()

            # Find the last trading day that is <= article date
            # We search backwards because we want the most recent trading day before/on article date
            last_trading_day = None
            for chart_date in reversed(chart_dates_range):
                # Normalize chart date for comparison
                if hasattr(chart_date, "normalize"):
                    chart_date_norm = chart_date.normalize()
                else:
                    chart_date_norm = pd.Timestamp(chart_date).normalize()

                # If this trading day is on or before the article date, use it
                if chart_date_norm <= article_date_norm:
                    last_trading_day = chart_date
                    break

            # Edge case: If no trading day found before article date (article is very old),
            # use the last available trading day as fallback
            if last_trading_day is None and chart_dates_range:
                last_trading_day = chart_dates_range[-1]

            return last_trading_day if last_trading_day is not None else article_date

        except Exception:
            # Robust fallback: if any date parsing fails, return original date
            return article_date  # Fallback to original date

    def _find_price_at_date(self, article_date, price_dates, prices):
        """Find the price and x-position closest to the article date"""
        try:
            if not price_dates or not prices:
                return None, None

            # Find closest date
            closest_idx = min(
                range(len(price_dates)),
                key=lambda i: abs((price_dates[i] - article_date).total_seconds()),
            )

            return prices[closest_idx], closest_idx

        except Exception:
            return None, None

    def _plot_articles_only(self, article_dates, article_sentiments):
        """Plot just article timeline when no price data available (legacy method)"""
        try:
            # Create a simple timeline with prominent markers for each article
            for i, sentiment in enumerate(article_sentiments):
                if sentiment > 0.1:
                    color = "green"
                    marker_symbol = "▲"  # Up triangle for positive
                elif sentiment < -0.1:
                    color = "red"
                    marker_symbol = "▼"  # Down triangle for negative
                else:
                    color = "yellow"
                    marker_symbol = "●"  # Circle for neutral

                # Draw thick vertical line for each article
                line_y_values = []
                line_x_values = []

                # Create multiple points for a thick vertical line
                for step in range(11):
                    y_val = step / 10  # From 0 to 1
                    line_y_values.append(y_val)
                    line_x_values.append(i)

                # Plot the vertical line
                self.plt.plot(
                    line_x_values, line_y_values, color=color, marker="braille"
                )

                # Add prominent marker at top
                self.plt.scatter([i], [1.1], color=color, marker=marker_symbol)

            # Format x-axis with actual publication dates
            if len(article_dates) > 0:
                x_ticks = list(range(len(article_dates)))
                x_labels = [
                    article_dates[i].strftime("%Y-%m-%d") for i in x_ticks
                ]  # Full calendar dates
                self.plt.xticks(x_ticks, x_labels)

                # Add date labels above each marker for clarity
                for i, article_date in enumerate(article_dates):
                    date_str = article_date.strftime("%m/%d")
                    try:
                        # Try to add text label above the marker
                        self.plt.text(date_str, i, 1.2)
                    except Exception:
                        # If text doesn't work, the x-axis labels will show the dates
                        pass

        except Exception:
            pass

    def _plot_focused_articles_only(self, article_dates, article_sentiments):
        """Plot FOCUSED article timeline when no price data available - enhanced for sentiment visibility"""
        try:
            if not article_dates or not article_sentiments:
                return

            # Sort articles by date for better timeline visualization
            sorted_data = sorted(
                zip(article_dates, article_sentiments), key=lambda x: x[0]
            )
            sorted_dates, sorted_sentiments = zip(*sorted_data)

            # Create enhanced timeline with better sentiment visualization
            for i, sentiment in enumerate(sorted_sentiments):
                # Enhanced sentiment color coding
                if sentiment > 0.1:
                    color = "green"
                    marker_symbol = "▲"  # Up triangle for positive
                elif sentiment < -0.1:
                    color = "red"
                    marker_symbol = "▼"  # Down triangle for negative
                else:
                    color = "yellow"
                    marker_symbol = "●"  # Circle for neutral

                # Create sentiment-based height for visual impact
                base_height = 0.5
                sentiment_height = base_height + (
                    sentiment * 0.3
                )  # Scale sentiment to height
                sentiment_height = max(
                    0.1, min(0.9, sentiment_height)
                )  # Clamp between 0.1 and 0.9

                # Draw enhanced vertical line with sentiment-based styling
                line_y_values = []
                line_x_values = []

                # Create multiple points for a thick vertical line from 0 to sentiment height
                for step in range(15):  # More points for smoother line
                    y_val = (step / 14) * sentiment_height  # Scale to sentiment height
                    line_y_values.append(y_val)
                    line_x_values.append(i)

                # Plot the vertical line
                self.plt.plot(
                    line_x_values, line_y_values, color=color, marker="braille"
                )

                # Add prominent marker at the sentiment height
                self.plt.scatter(
                    [i], [sentiment_height], color=color, marker=marker_symbol
                )

                # Add additional markers for maximum visibility
                self.plt.scatter(
                    [i], [sentiment_height + 0.05], color=color, marker=marker_symbol
                )
                self.plt.scatter(
                    [i], [sentiment_height - 0.05], color=color, marker=marker_symbol
                )

            # Enhanced x-axis formatting for focused view
            if len(sorted_dates) > 0:
                x_ticks = list(range(len(sorted_dates)))
                # Use more detailed date format for focused view
                x_labels = [sorted_dates[i].strftime("%m/%d %H:%M") for i in x_ticks]
                self.plt.xticks(x_ticks, x_labels)

            # Set appropriate y-axis range for sentiment visualization
            self.plt.ylim(0, 1.2)

        except Exception:
            pass

    def _interpolate_price_for_date(self, article_date, chart_dates, chart_prices):
        """Find the price at or closest to the article publication date"""
        try:
            import pandas as pd

            if not chart_dates or not chart_prices:
                return None

            # Convert to pandas for easier date handling
            price_series = pd.Series(chart_prices, index=chart_dates)

            # Find the closest date
            closest_date = min(
                chart_dates, key=lambda x: abs((x - article_date).total_seconds())
            )

            # Return the price at that date
            return price_series[closest_date]

        except Exception:
            return None

    def _get_x_position_for_date(self, article_date, chart_dates):
        """Get the x-axis position for the article date on the chart"""
        try:
            if not chart_dates:
                return None

            # Find the closest date index
            closest_idx = min(
                range(len(chart_dates)),
                key=lambda i: abs((chart_dates[i] - article_date).total_seconds()),
            )

            return closest_idx

        except Exception:
            return None


class TickerNewsPanel(Vertical):
    """Panel displaying news articles and timeline chart for the selected ticker"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_ticker = None

    def compose(self) -> ComposeResult:
        # News articles table (full height)
        with ScrollableContainer(id="news-table-container", classes="news-table-panel"):
            yield Static(
                "📊 Select a ticker to view related news articles",
                id="ticker-news-placeholder",
            )
            yield TickerNewsTable(id="ticker-news-table", classes="hidden")

    def update_ticker_news(
        self, ticker_symbol: str, news_data: List[Dict], sentiment_details: List[Dict]
    ):
        """Update the news panel with articles related to the selected ticker"""
        self.current_ticker = ticker_symbol

        # Filter news articles that mention this ticker using the sophisticated detection
        # that was already computed during sentiment analysis
        ticker_articles = []
        for i, article in enumerate(news_data):
            # Check if ticker is mentioned using the pre-computed mentioned_tickers list
            if i < len(sentiment_details):
                mentioned_tickers = sentiment_details[i].get("mentioned_tickers", [])
                if ticker_symbol in mentioned_tickers:
                    article_data = {
                        "article": article,
                        "sentiment_detail": sentiment_details[i],
                        "index": i,
                    }
                    ticker_articles.append(article_data)

        # Get the table and placeholder widgets
        news_table = self.query_one("#ticker-news-table", TickerNewsTable)
        placeholder = self.query_one("#ticker-news-placeholder", Static)

        if not ticker_articles:
            # Show placeholder, hide table
            placeholder.update(f"📰 No recent news articles found for {ticker_symbol}")
            placeholder.remove_class("hidden")
            news_table.add_class("hidden")
            return

        # Hide placeholder, show table
        placeholder.add_class("hidden")
        news_table.remove_class("hidden")

        # Clear and populate the table
        news_table.clear()
        news_table.articles_data = ticker_articles  # Store for row selection

        for i, article_data in enumerate(ticker_articles, 1):
            article = article_data["article"]
            sentiment_detail = article_data["sentiment_detail"]

            headline = article.get("headline", "No headline")
            time_ago = article.get(
                "time_ago", "Unknown time"
            )  # Keep relative time for table
            sentiment_score = sentiment_detail.get("polarity", 0)

            # Sentiment styling and text
            if sentiment_score > 0.1:
                sentiment_emoji = "🟢"
                sentiment_style = "green"
                sentiment_text = "Positive"
            elif sentiment_score < -0.1:
                sentiment_emoji = "🔴"
                sentiment_style = "red"
                sentiment_text = "Negative"
            else:
                sentiment_emoji = "🟡"
                sentiment_style = "yellow"
                sentiment_text = "Neutral"

            # Add row to table
            news_table.add_row(
                str(i),
                headline[:80],  # Truncate long headlines
                time_ago,  # Keep relative time for easy readability
                Text(f"{sentiment_emoji} {sentiment_text}", style=sentiment_style),
                Text(f"{sentiment_score:+.3f}", style=sentiment_style),
            )


class InteractiveTickerTable(DataTable):
    """Interactive data table for tickers with sorting and filtering"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.show_cursor = True

    def on_mount(self) -> None:
        self.add_columns(
            "Rank", "Ticker", "Price", "Change", "Sentiment", "Articles", "Sector"
        )

    def update_data(
        self, ticker_rankings: List[Dict], price_changes: Dict, current_prices: Dict
    ):
        """Update table with ALL ticker data including proper sector information"""
        from ..core.sentiment_analyzer import get_ticker_sector

        self.clear()

        # Get cached sentiment details for accurate article counting
        sentiment_details = []
        if hasattr(self.app, "data_cache") and self.app.data_cache:
            sentiment_details = self.app.data_cache.get("sentiment_details", [])

        # Show ALL tickers, not just top 25
        for i, ticker in enumerate(ticker_rankings, 1):
            ticker_symbol = ticker["ticker"]
            price_change = price_changes.get(ticker_symbol, 0.0)
            current_price = current_prices.get(ticker_symbol, 0.0)

            # Get sector information using the sector mapping
            sector = get_ticker_sector(ticker_symbol)

            # Count articles that actually mention this ticker using the sophisticated detection
            # that was already computed during sentiment analysis
            ticker_article_count = 0
            for detail in sentiment_details:
                mentioned_tickers = detail.get("mentioned_tickers", [])
                if ticker_symbol in mentioned_tickers:
                    ticker_article_count += 1

            # Color coding for sentiment (standardized thresholds)
            sentiment_score = ticker["overall_score"]
            if sentiment_score > 0.1:
                sentiment_color = "green"
            elif sentiment_score < -0.1:
                sentiment_color = "red"
            else:
                sentiment_color = "yellow"

            # Price change emoji and color
            if price_change > 0:
                price_emoji = "📈"
                price_color = "green"
            elif price_change < 0:
                price_emoji = "📉"
                price_color = "red"
            else:
                price_emoji = "➡️"
                price_color = "white"

            self.add_row(
                str(i),
                ticker_symbol,
                f"${current_price:.2f}",
                Text(f"{price_emoji} {price_change:+.1f}%", style=price_color),
                Text(f"{sentiment_score:.3f}", style=sentiment_color),
                str(
                    ticker_article_count
                ),  # Use the actual count of articles that mention this ticker
                sector[:12],  # Show more of the sector name
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - update right panel with detailed ticker information"""
        from ..core.sentiment_analyzer import get_ticker_sector

        row_data = self.get_row_at(event.cursor_row)
        if row_data:
            ticker_symbol = str(row_data[1])
            # Get the full sector name from the mapping
            sector = get_ticker_sector(ticker_symbol)

            # Extract sentiment value from Text object
            sentiment_text = row_data[4]
            if hasattr(sentiment_text, "plain"):
                sentiment_value = float(sentiment_text.plain)
            else:
                # Fallback for string representation
                sentiment_value = float(str(sentiment_text))

            # Get company name from app's data cache
            company_name = ticker_symbol  # Default fallback
            if hasattr(self.app, "data_cache") and self.app.data_cache:
                company_names = self.app.data_cache.get("company_names", {})
                company_name = company_names.get(ticker_symbol, ticker_symbol)

            ticker_data = {
                "ticker": ticker_symbol,
                "company_name": company_name,
                "price": float(str(row_data[2]).replace("$", "")),
                "sentiment": sentiment_value,
                "articles": int(str(row_data[5])),
                "sector": sector,  # Use the full sector name
                "rank": int(str(row_data[0])),  # Rank column
                "price_change": str(row_data[3]),  # Price change column
            }

            # Update the right panel instead of showing a modal
            self._update_ticker_details_panel(ticker_data)

    def _update_ticker_details_panel(self, ticker_data):
        """Update the ticker details panel in the right pane with comprehensive ticker information"""
        try:
            # Update ticker info panel
            ticker_info = self.app.query_one("#ticker-info", Static)
            info_content = self._create_ticker_info_content(ticker_data)
            ticker_info.update(info_content)

            # Update earnings panel
            ticker_earnings = self.app.query_one("#ticker-earnings", Static)
            earnings_content = self._create_ticker_earnings_content(ticker_data)
            ticker_earnings.update(earnings_content)

            # Update the chart widget
            self._update_ticker_chart(ticker_data)

            # Update the news panel with ticker-specific news
            self._update_ticker_news_panel(ticker_data)

            # Force refresh of the chart widget to fix rendering issues
            try:
                chart_widget = self.app.query_one("#ticker-chart", PlotextPlot)
                # Schedule a refresh to ensure the chart renders properly
                self.app.call_later(lambda: chart_widget.refresh())
            except Exception:
                pass

        except Exception:
            # Fallback if panel not found
            pass

    def _create_ticker_info_content(self, ticker_data):
        """Create rich content for the ticker info panel (basic info only)"""
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        # Basic ticker information
        ticker_symbol = ticker_data.get("ticker", "N/A")
        company_name = ticker_data.get("company_name", ticker_symbol)
        price = ticker_data.get("price", 0)
        sentiment = ticker_data.get("sentiment", 0)
        articles = ticker_data.get("articles", 0)
        sector = ticker_data.get("sector", "N/A")
        rank = ticker_data.get("rank", "N/A")
        price_change = ticker_data.get("price_change", "N/A")

        # Create a table for the info panel
        table = Table.grid(padding=0)
        table.add_column("Field", style="bold cyan", width=16)
        table.add_column("Value", width=32)

        # Company Header - Prominent display
        if company_name and company_name != ticker_symbol:
            # Use available space for company name
            display_name = (
                company_name[:45] + "..." if len(company_name) > 45 else company_name
            )
            table.add_row("🏢 Company:", Text(display_name, style="bold white"))
        else:
            table.add_row("🏢 Company:", Text(ticker_symbol, style="bold white"))

        table.add_row("📈 Symbol:", Text(ticker_symbol, style="bold cyan"))
        table.add_row("🏆 Rank:", f"#{rank}")

        # Price information
        table.add_row("💵 Price:", f"${price:.2f}")

        # Parse price change for better display
        if price_change and price_change != "N/A":
            if "📈" in price_change:
                change_style = "green"
            elif "📉" in price_change:
                change_style = "red"
            else:
                change_style = "yellow"
            table.add_row("📊 Change:", Text(price_change, style=change_style))

        # Performance indicator
        if rank != "N/A":
            rank_num = int(rank)
            if rank_num <= 5:
                performance = "🌟 Top Performer"
                perf_style = "green"
            elif rank_num <= 15:
                performance = "📈 Strong"
                perf_style = "green"
            elif rank_num <= 30:
                performance = "📊 Average"
                perf_style = "yellow"
            else:
                performance = "📉 Below Avg"
                perf_style = "red"
            table.add_row("🏆 Performance:", Text(performance, style=perf_style))

        # Sentiment Analysis
        if sentiment > 0.3:
            sentiment_style = "green"
            sentiment_emoji = "🟢"
            sentiment_desc = "Very Positive"
        elif sentiment > 0.1:
            sentiment_style = "green"
            sentiment_emoji = "🟢"
            sentiment_desc = "Positive"
        elif sentiment > -0.1:
            sentiment_style = "yellow"
            sentiment_emoji = "🟡"
            sentiment_desc = "Neutral"
        elif sentiment > -0.3:
            sentiment_style = "red"
            sentiment_emoji = "🔴"
            sentiment_desc = "Negative"
        else:
            sentiment_style = "red"
            sentiment_emoji = "🔴"
            sentiment_desc = "Very Negative"

        table.add_row(
            "🎯 Sentiment:",
            Text(f"{sentiment_emoji} {sentiment:.3f}", style=sentiment_style),
        )
        table.add_row("📝 Category:", Text(sentiment_desc, style=sentiment_style))
        table.add_row("📰 Articles:", f"{articles} analyzed")
        table.add_row("🏢 Sector:", sector)

        # Investment recommendation
        if sentiment > 0.2 and rank != "N/A" and int(rank) <= 10:
            recommendation = "🟢 Strong Buy"
            rec_style = "green"
        elif sentiment > 0.1 and rank != "N/A" and int(rank) <= 20:
            recommendation = "🟡 Moderate Buy"
            rec_style = "yellow"
        elif sentiment < -0.1:
            recommendation = "🔴 Caution"
            rec_style = "red"
        else:
            recommendation = "⚪ Hold/Monitor"
            rec_style = "white"

        table.add_row("💡 Signal:", Text(recommendation, style=rec_style))

        # Return the table wrapped in a panel with title
        return Panel(table, title="📊 Ticker Info", border_style="cyan")

    def _create_ticker_earnings_content(self, ticker_data):
        """Create rich content for the earnings panel (earnings data only)"""
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        ticker_symbol = ticker_data.get("ticker", "N/A")

        # Create a table for earnings data
        table = Table.grid(padding=0)
        table.add_column("Field", style="bold cyan", width=16)
        table.add_column("Value", width=32)

        # Add earnings data if available
        try:
            from ..core.earnings_fetcher import get_earnings_summary_for_ticker

            earnings_summary = get_earnings_summary_for_ticker(ticker_symbol)

            if earnings_summary and earnings_summary.get("status") == "success":

                latest_quarter = earnings_summary.get("latest_quarter")
                if latest_quarter:
                    quarter_name = latest_quarter.get("quarter", "N/A")
                    revenue = latest_quarter.get("metrics", {}).get("revenue", 0)
                    net_income = latest_quarter.get("metrics", {}).get("net_income", 0)

                    table.add_row("📅 Quarter:", quarter_name)

                    if revenue:
                        revenue_str = (
                            f"${revenue/1e9:.1f}B"
                            if revenue > 1e9
                            else f"${revenue/1e6:.0f}M"
                        )
                        table.add_row("💰 Revenue:", revenue_str)

                    if net_income:
                        income_str = (
                            f"${net_income/1e9:.1f}B"
                            if abs(net_income) > 1e9
                            else f"${net_income/1e6:.0f}M"
                        )
                        table.add_row("💵 Net Income:", income_str)

                    # Calculate and show profit margin
                    if revenue and revenue > 0:
                        margin = (net_income / revenue) * 100
                        margin_style = (
                            "green"
                            if margin > 10
                            else "yellow" if margin > 0 else "red"
                        )
                        table.add_row(
                            "📊 Margin:", Text(f"{margin:.1f}%", style=margin_style)
                        )

                    # Show earnings trends
                    analysis = earnings_summary.get("analysis", {})
                    trends = analysis.get("trends", {})

                    if trends:
                        revenue_trend = trends.get("revenue", {})
                        income_trend = trends.get("net_income", {})

                        if revenue_trend:
                            trend_name = revenue_trend.get("trend", "stable")
                            trend_emoji = (
                                "📈"
                                if trend_name == "improving"
                                else "📉" if trend_name == "declining" else "➡️"
                            )
                            avg_growth = revenue_trend.get("avg_growth", 0)
                            table.add_row(
                                "📈 Rev Trend:",
                                Text(
                                    f"{trend_emoji} {trend_name.title()} ({avg_growth:+.1f}%)",
                                    style=(
                                        "green"
                                        if trend_name == "improving"
                                        else (
                                            "red"
                                            if trend_name == "declining"
                                            else "yellow"
                                        )
                                    ),
                                ),
                            )

                        if income_trend:
                            trend_name = income_trend.get("trend", "stable")
                            trend_emoji = (
                                "📈"
                                if trend_name == "improving"
                                else "📉" if trend_name == "declining" else "➡️"
                            )
                            avg_growth = income_trend.get("avg_growth", 0)
                            table.add_row(
                                "💵 Inc Trend:",
                                Text(
                                    f"{trend_emoji} {trend_name.title()} ({avg_growth:+.1f}%)",
                                    style=(
                                        "green"
                                        if trend_name == "improving"
                                        else (
                                            "red"
                                            if trend_name == "declining"
                                            else "yellow"
                                        )
                                    ),
                                ),
                            )

                    # Overall earnings performance
                    performance = analysis.get("performance", {}).get(
                        "overall", "unknown"
                    )
                    if performance != "unknown":
                        perf_emoji = (
                            "🟢"
                            if performance == "strong"
                            else "🔴" if performance == "weak" else "🟡"
                        )
                        perf_style = (
                            "green"
                            if performance == "strong"
                            else "red" if performance == "weak" else "yellow"
                        )
                        table.add_row(
                            "🏆 Overall:",
                            Text(
                                f"{perf_emoji} {performance.title()}", style=perf_style
                            ),
                        )
            else:
                table.add_row("📊 Status:", "No data available")

        except Exception:
            table.add_row("📊 Status:", "Error loading data")

        # Return the table wrapped in a panel with title
        return Panel(table, title="💰 Earnings", border_style="yellow")

    def _update_ticker_chart(self, ticker_data):
        """Update the PlotextPlot widget with price history and article markers for the selected ticker"""
        try:
            # Find the chart widget
            chart_widget = self.app.query_one("#ticker-chart", PlotextPlot)

            ticker_symbol = ticker_data.get("ticker", "N/A")
            prices, dates = self._get_ticker_price_history(ticker_symbol)

            if len(prices) < 2:
                # Clear the chart if no data
                chart_widget.plt.clear_data()
                chart_widget.plt.clear_figure()
                chart_widget.plt.text(
                    0.5, 0.5, "No price data available", alignment="center"
                )
                chart_widget.plt.title(f"{ticker_symbol} - No Data")
                chart_widget.plt.plotsize(80, 12)  # Consistent sizing even for no data
                chart_widget.refresh()  # Force refresh
                return

            # Clear previous plot
            chart_widget.plt.clear_data()
            chart_widget.plt.clear_figure()

            # Use 6 months of data (approximately 130 trading days)
            # Take all available data up to 6 months
            chart_prices = prices[-130:] if len(prices) >= 130 else prices
            chart_dates_raw = dates[-130:] if dates and len(dates) >= 130 else dates

            # Get article data for this ticker
            article_dates, article_sentiments = self._get_ticker_article_dates(
                ticker_symbol, chart_dates_raw
            )

            # Get earnings dates for this ticker
            earnings_dates = self._get_ticker_earnings_dates(
                ticker_symbol, chart_dates_raw
            )

            # Convert dates to strings for x-axis labels
            if chart_dates_raw:
                # Format dates as MM/DD for better readability
                date_labels = []
                for date in chart_dates_raw:
                    if hasattr(date, "strftime"):
                        date_labels.append(date.strftime("%m/%d"))
                    else:
                        date_labels.append(str(date))

                # Use numeric sequence for plotting, but set custom labels
                chart_x_values = list(range(len(chart_prices)))

                # Create the plot with enhanced styling for wider charts (matching Market Indices style)
                chart_widget.plt.plot(
                    chart_x_values,
                    chart_prices,
                    marker="braille",
                    color="cyan",
                    fillx=True,
                )

                # Add article markers if we have article data with stacking
                if article_dates and article_sentiments:
                    # Group articles by date for stacking
                    articles_by_date = {}
                    for article_date, sentiment in zip(
                        article_dates, article_sentiments
                    ):
                        date_key = article_date.date()
                        if date_key not in articles_by_date:
                            articles_by_date[date_key] = []
                        articles_by_date[date_key].append((article_date, sentiment))

                    # Plot article markers with sentiment-based colors and stacking
                    for date_key, articles_on_date in articles_by_date.items():
                        x_pos = None
                        price_for_date = None

                        # Find x position and price for this date
                        for j, date in enumerate(chart_dates_raw):
                            if date.date() == date_key:
                                x_pos = j
                                price_for_date = chart_prices[j]
                                break

                        if x_pos is not None and price_for_date is not None:
                            # Calculate price range for stacking with enhanced visibility
                            price_range = max(chart_prices) - min(chart_prices)
                            stack_offset = (
                                price_range * 0.03
                            )  # 3% of price range per stack level for better visibility

                            # Debug logging for stacking
                            if (
                                hasattr(self.app, "verbose_mode")
                                and self.app.verbose_mode
                            ):
                                print(
                                    f"🔍 DETAILS STACKING DEBUG: {len(articles_on_date)} articles on {date_key}, stack_offset={stack_offset:.2f}"
                                )

                            # Sort articles by sentiment for proper layering (neutral first, then positive/negative on top)
                            # This ensures colored triangles are visible on top of neutral circles
                            def sentiment_sort_key(article):
                                sentiment = article[1]
                                if (
                                    abs(sentiment) <= 0.1
                                ):  # Neutral articles first (bottom layer) - standardized threshold
                                    return (0, sentiment)
                                else:  # Positive/negative articles last (top layer)
                                    return (1, sentiment)

                            articles_on_date.sort(key=sentiment_sort_key)

                            for stack_index, (_, sentiment) in enumerate(
                                articles_on_date
                            ):
                                # Calculate stacked position first
                                total_articles = len(articles_on_date)
                                center_offset = (total_articles - 1) * stack_offset / 2
                                stacked_price = (
                                    price_for_date
                                    + (stack_index * stack_offset)
                                    - center_offset
                                )

                                # Clean sentiment visualization with distinct shapes
                                print(
                                    f"🎯 MAIN CHART DEBUG: Article sentiment = {sentiment:.3f}"
                                )
                                if (
                                    sentiment > 0.1
                                ):  # Positive sentiment (standardized threshold)
                                    # Green triangle pointing up for positive news
                                    marker_color = (0, 255, 0)  # Bright green RGB
                                    marker_symbol = "▲"
                                    print(
                                        f"🎯 MAIN CHART DEBUG: Using GREEN TRIANGLE ▲ for positive sentiment {sentiment:.3f}"
                                    )

                                elif (
                                    sentiment < -0.1
                                ):  # Negative sentiment (standardized threshold)
                                    # Red triangle pointing down for negative news
                                    marker_color = (255, 0, 0)  # Bright red RGB
                                    marker_symbol = "▼"
                                    print(
                                        f"🎯 MAIN CHART DEBUG: Using RED TRIANGLE ▼ for negative sentiment {sentiment:.3f}"
                                    )

                                else:  # Neutral sentiment
                                    # Yellow circle for neutral news
                                    marker_color = (255, 255, 0)  # Bright yellow RGB
                                    marker_symbol = "●"
                                    print(
                                        f"🎯 MAIN CHART DEBUG: Using YELLOW CIRCLE ● for neutral sentiment {sentiment:.3f}"
                                    )

                                # Plot single clear marker for each article
                                chart_widget.plt.scatter(
                                    [x_pos],
                                    [stacked_price],
                                    marker=marker_symbol,
                                    color=marker_color,
                                )

                    # Create article data for influence lines (use original approach)
                    article_data = list(zip(article_dates, article_sentiments))
                    article_data.sort(key=lambda x: x[0])  # Sort by date

                    # Plot influence sections
                    for i, (_, _) in enumerate(article_data):
                        # Add influence section line (vertical line from this article to next)
                        if (
                            len(chart_prices) > 0 and len(chart_dates_raw) > 0
                        ):  # Ensure we have data
                            if i < len(article_data) - 1:  # Not the last article
                                next_article_date = article_data[i + 1][0]
                                next_x_pos = self._get_x_position_for_date(
                                    next_article_date, chart_dates_raw
                                )
                                if next_x_pos is not None and next_x_pos > 0:
                                    # Draw vertical line at the end of this article's influence period
                                    influence_x = max(
                                        0, next_x_pos - 0.5
                                    )  # Slightly before next article
                                    min_price = min(chart_prices)
                                    max_price = max(chart_prices)

                                    # Draw influence section line
                                    try:
                                        influence_y_values = [min_price, max_price]
                                        influence_x_values = [influence_x, influence_x]
                                        chart_widget.plt.plot(
                                            influence_x_values,
                                            influence_y_values,
                                            color="gray",
                                            marker="",
                                            linestyle="--",
                                        )
                                    except Exception:
                                        pass  # Skip if plotting fails
                            else:
                                # Last article - draw line to end of chart
                                if len(chart_dates_raw) > 1:
                                    end_x = len(chart_dates_raw) - 1
                                    min_price = min(chart_prices)
                                    max_price = max(chart_prices)

                                    # Draw final influence section line
                                    try:
                                        influence_y_values = [min_price, max_price]
                                        influence_x_values = [end_x, end_x]
                                        chart_widget.plt.plot(
                                            influence_x_values,
                                            influence_y_values,
                                            color="gray",
                                            marker="",
                                            linestyle="--",
                                        )
                                    except Exception:
                                        pass  # Skip if plotting fails

                # Add earnings date markers using EXACT same approach as articles
                if earnings_dates:
                    for earnings_date, _quarter_label in earnings_dates:
                        # Find x position for earnings date (same as articles)
                        earnings_x_pos = self._get_x_position_for_date(
                            earnings_date, chart_dates_raw
                        )

                        if earnings_x_pos is not None:
                            try:
                                # Find the price at this date for positioning (same as articles)
                                price_for_date = None
                                for j, _ in enumerate(chart_dates_raw):
                                    if j == earnings_x_pos:
                                        price_for_date = chart_prices[j]
                                        break

                                if price_for_date is not None:
                                    # Position earnings marker at top of chart for visibility
                                    earnings_price = (
                                        max_price * 0.95
                                    )  # Near top like articles

                                    # Use EXACT same scatter approach as articles with distinct marker
                                    # Yellow diamond for earnings (different from article triangles/circles)
                                    marker_color = (
                                        255,
                                        255,
                                        0,
                                    )  # Bright yellow RGB (same format as articles)
                                    marker_symbol = "♦"  # Diamond symbol for earnings

                                    # Plot single clear marker for earnings (EXACT same as articles)
                                    chart_widget.plt.scatter(
                                        [earnings_x_pos],
                                        [earnings_price],
                                        marker=marker_symbol,
                                        color=marker_color,
                                    )

                                    # Earnings marker ♦ plotted successfully for quarter_label

                            except Exception as e:
                                print(f"⚠️ Error plotting earnings marker: {e}")

                # Set custom x-axis labels for wider charts - show more labels
                step = max(
                    1, len(date_labels) // 12
                )  # Show about 12 labels for wider view
                x_ticks = list(range(0, len(date_labels), step))
                x_labels = [date_labels[i] for i in x_ticks]

                chart_widget.plt.xticks(x_ticks, x_labels)

                # Set chart dimensions for better visibility (matching Market Indices)
                chart_widget.plt.plotsize(80, 12)  # Wider plot for better detail
            else:
                # Fallback to numeric sequence if no dates
                chart_x_values = list(range(len(chart_prices)))
                chart_widget.plt.plot(
                    chart_x_values,
                    chart_prices,
                    marker="braille",
                    color="cyan",
                    fillx=True,
                )
                chart_widget.plt.plotsize(80, 12)  # Consistent sizing

            # Configure the plot with enhanced styling
            # Show price range and article count in title for context
            min_price = min(chart_prices)
            max_price = max(chart_prices)
            price_range = f"Range: ${min_price:.2f} - ${max_price:.2f}"
            article_count = len(article_dates) if article_dates else 0
            earnings_count = len(earnings_dates) if earnings_dates else 0
            chart_widget.plt.title(
                f"{ticker_symbol} - 6 Month History | {price_range} | {article_count} Articles | {earnings_count} Earnings"
            )
            chart_widget.plt.xlabel("Date")
            chart_widget.plt.ylabel("Price ($)")

            # Add grid for better readability
            chart_widget.plt.grid(True, True)

            # Force refresh to fix rendering issue
            chart_widget.refresh()

            # The PlotextPlot widget will handle the rendering automatically

        except Exception:
            # Fallback if chart widget not found
            pass

    def _get_ticker_price_history(self, ticker_symbol):
        """Fetch price history for the ticker to display in chart"""
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker_symbol)
            # Get 6 months of history for comprehensive chart
            hist = stock.history(period="6mo")

            if not hist.empty:
                # Return list of closing prices
                prices = hist["Close"].tolist()
                dates = hist.index.tolist()
                return prices, dates
            else:
                return [], []
        except Exception:
            return [], []

    def _get_ticker_article_dates(self, ticker_symbol, chart_dates_range):
        """Get article publication dates and sentiments for the ticker within the chart date range"""
        try:
            import pandas as pd

            # Get news data from app cache
            if not hasattr(self.app, "data_cache") or not self.app.data_cache:
                return [], []

            news_data = self.app.data_cache.get("news_data", [])
            sentiment_details = self.app.data_cache.get("sentiment_details", [])

            if not news_data or not sentiment_details:
                return [], []

            # Get the date range for filtering
            if not chart_dates_range:
                return [], []

            start_date = chart_dates_range[0]
            end_date = chart_dates_range[-1]

            article_dates = []
            article_sentiments = []

            # Filter articles that mention this ticker and are within date range
            for i, article in enumerate(news_data):
                if i >= len(sentiment_details):
                    continue

                # Check if ticker is mentioned using the pre-computed mentioned_tickers list
                mentioned_tickers = sentiment_details[i].get("mentioned_tickers", [])
                if ticker_symbol not in mentioned_tickers:
                    continue

                # Get article publication date
                pub_timestamp = article.get("pub_timestamp")
                if not pub_timestamp:
                    continue

                # Convert timestamp to datetime
                try:
                    article_date = pd.to_datetime(pub_timestamp, unit="s").tz_localize(
                        "UTC"
                    )
                    # Convert to same timezone as chart dates if needed
                    if hasattr(start_date, "tz") and start_date.tz:
                        article_date = article_date.tz_convert(start_date.tz)
                    else:
                        article_date = article_date.tz_localize(None)

                    # Check if article is within chart date range
                    if start_date <= article_date <= end_date:
                        article_dates.append(article_date)
                        # Get sentiment score
                        sentiment_score = sentiment_details[i].get("polarity", 0)
                        article_sentiments.append(sentiment_score)

                except Exception:
                    continue

            return article_dates, article_sentiments

        except Exception:
            return [], []

    def _interpolate_price_for_date(self, article_date, chart_dates, chart_prices):
        """Find the price at or closest to the article publication date"""
        try:
            import pandas as pd

            if not chart_dates or not chart_prices:
                return None

            # Convert to pandas for easier date handling
            price_series = pd.Series(chart_prices, index=chart_dates)

            # Find the closest date
            closest_date = min(
                chart_dates, key=lambda x: abs((x - article_date).total_seconds())
            )

            # Return the price at that date
            return price_series[closest_date]

        except Exception:
            return None

    def _get_x_position_for_date(self, article_date, chart_dates):
        """Get the x-axis position for the article date on the chart"""
        try:
            if not chart_dates:
                return None

            # Find the closest date index
            closest_idx = min(
                range(len(chart_dates)),
                key=lambda i: abs((chart_dates[i] - article_date).total_seconds()),
            )

            return closest_idx

        except Exception:
            return None

    def _get_ticker_earnings_dates(self, ticker_symbol, chart_dates_range):
        """Get earnings announcement dates for the ticker within the chart date range"""
        try:
            from ..core.earnings_fetcher import cached_get_ticker_earnings_dates

            if not chart_dates_range:
                return []

            # Calculate date range in months (6 months for chart)
            date_range_months = 6

            # Get earnings dates from our earnings fetcher
            earnings_dates = cached_get_ticker_earnings_dates(
                ticker_symbol, date_range_months
            )

            if not earnings_dates:
                return []

            # Filter earnings dates to only those within the chart date range
            start_date = chart_dates_range[0]
            end_date = chart_dates_range[-1]

            filtered_earnings = []
            for earnings_date, quarter_label in earnings_dates:
                # Convert earnings date to same timezone as chart dates if needed
                if hasattr(start_date, "tz") and start_date.tz:
                    if earnings_date.tzinfo is None:
                        earnings_date = earnings_date.replace(tzinfo=start_date.tz)
                    else:
                        earnings_date = earnings_date.astimezone(start_date.tz)
                else:
                    # Remove timezone info if chart dates don't have it
                    if earnings_date.tzinfo is not None:
                        earnings_date = earnings_date.replace(tzinfo=None)

                # Check if earnings date is within chart range
                if start_date <= earnings_date <= end_date:
                    filtered_earnings.append((earnings_date, quarter_label))

            # Found earnings dates for ticker in chart range
            return filtered_earnings

        except Exception as e:
            print(f"⚠️ Error fetching earnings dates for {ticker_symbol}: {e}")
            return []

    def _update_ticker_news_panel(self, ticker_data):
        """Update the ticker news panel with articles related to the selected ticker"""
        try:
            ticker_symbol = ticker_data.get("ticker", "")
            if not ticker_symbol:
                return

            # Get news data from app cache
            if hasattr(self.app, "data_cache") and self.app.data_cache:
                news_data = self.app.data_cache.get("news_data", [])
                sentiment_details = self.app.data_cache.get("sentiment_details", [])

                # Find the ticker news panel and update it
                ticker_news_panel = self.app.query_one(
                    "#ticker-news-panel", TickerNewsPanel
                )
                ticker_news_panel.update_ticker_news(
                    ticker_symbol, news_data, sentiment_details
                )
        except Exception:
            # Handle errors gracefully
            pass


class RealTimeChart(Static):
    """Real-time sentiment chart using ASCII/Unicode characters"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sentiment_history = []
        self.border_title = "📈 Sentiment Trend"

    def update_sentiment(self, sentiment_score: float):
        """Add new sentiment data point"""
        self.sentiment_history.append(sentiment_score)
        if len(self.sentiment_history) > 50:  # Keep last 50 points
            self.sentiment_history.pop(0)

        self._render_chart()

    def _render_chart(self):
        """Render the ASCII chart"""
        if len(self.sentiment_history) < 2:
            self.update("📈 Collecting data...")
            return

        # Create simple sparkline chart
        chart_chars = "▁▂▃▄▅▆▇█"
        chart_data = []

        # Normalize data to 0-7 range for chart characters
        min_val = min(self.sentiment_history)
        max_val = max(self.sentiment_history)

        if max_val == min_val:
            # All values are the same
            chart_data = ["▄"] * len(self.sentiment_history[-30:])
        else:
            for val in self.sentiment_history[-30:]:
                normalized = (val - min_val) / (max_val - min_val)
                char_index = min(7, max(0, int(normalized * 7)))
                chart_data.append(chart_chars[char_index])

        # Create chart display
        chart_line = "".join(chart_data)
        current_val = self.sentiment_history[-1]

        # Determine trend
        if len(self.sentiment_history) >= 2:
            trend = (
                "📈"
                if self.sentiment_history[-1] > self.sentiment_history[-2]
                else "📉"
            )
        else:
            trend = "➡️"

        chart_text = f"Trend: {chart_line}\n"
        chart_text += f"Current: {current_val:+.3f} {trend}\n"
        chart_text += f"Range: {min_val:.3f} to {max_val:.3f}"

        self.update(Panel(chart_text, title="📈 Live Sentiment"))


class NewsTreeView(Tree):
    """Interactive tree view for news articles organized by sentiment"""

    def __init__(self, **kwargs):
        super().__init__("📰 Recent News", **kwargs)
        self.show_root = False

    def update_news(
        self,
        news_data: List[Dict],
        sentiment_scores: List[float],
        sentiment_details: List[Dict],
    ):
        """Update tree with news data organized by sentiment, showing all analyzed articles with their tickers"""
        self.clear()

        # Create sentiment category nodes
        positive_node = self.root.add("🟢 Positive News", expand=True)
        neutral_node = self.root.add("🟡 Neutral News", expand=True)
        negative_node = self.root.add("🔴 Negative News", expand=True)

        # Process all analyzed articles (not just first 20)
        max_articles = min(
            len(news_data), len(sentiment_scores), len(sentiment_details)
        )
        combined_data = list(
            zip(
                news_data[:max_articles],
                sentiment_scores[:max_articles],
                sentiment_details[:max_articles],
            )
        )

        # Sort by time (most recent first) to show latest news at top
        combined_data.sort(key=lambda x: x[0].get("pub_timestamp", 0), reverse=True)

        for article, sentiment, detail in combined_data:
            headline = article["headline"]
            if len(headline) > 55:
                headline = headline[:52] + "..."

            # Get all mentioned tickers for this article
            mentioned_tickers = detail.get("mentioned_tickers", [])
            primary_ticker = article.get("ticker", "N/A")
            time_ago = article.get("time_ago", "Unknown")

            # Create comprehensive ticker display
            if mentioned_tickers and len(mentioned_tickers) > 1:
                # Multi-ticker article - show all tickers with sentiment indicators
                ticker_sentiments = detail.get("ticker_sentiments", {})
                ticker_parts = []

                for ticker in mentioned_tickers[:5]:  # Show up to 5 tickers
                    if ticker in ticker_sentiments:
                        ticker_sentiment = ticker_sentiments[ticker]
                        sentiment_cat = ticker_sentiment.get(
                            "sentiment_category", "Neutral"
                        )
                        if sentiment_cat == "Positive":
                            ticker_emoji = "🟢"
                        elif sentiment_cat == "Negative":
                            ticker_emoji = "🔴"
                        else:
                            ticker_emoji = "🟡"
                        ticker_parts.append(f"{ticker_emoji}{ticker}")
                    else:
                        ticker_parts.append(f"⚪{ticker}")

                if len(mentioned_tickers) > 5:
                    ticker_parts.append(f"+{len(mentioned_tickers)-5}")

                ticker_display = " ".join(ticker_parts)
            elif mentioned_tickers and len(mentioned_tickers) == 1:
                # Single ticker from analysis
                ticker = mentioned_tickers[0]
                ticker_sentiments = detail.get("ticker_sentiments", {})
                if ticker in ticker_sentiments:
                    sentiment_cat = ticker_sentiments[ticker].get(
                        "sentiment_category", "Neutral"
                    )
                    if sentiment_cat == "Positive":
                        ticker_emoji = "🟢"
                    elif sentiment_cat == "Negative":
                        ticker_emoji = "🔴"
                    else:
                        ticker_emoji = "🟡"
                    ticker_display = f"{ticker_emoji}{ticker}"
                else:
                    ticker_display = f"⚪{ticker}"
            else:
                # Fallback to primary ticker
                ticker_display = f"📊{primary_ticker}"

            # Create node text with comprehensive ticker information
            node_text = f"[{time_ago}] {ticker_display}: {headline}"

            # Add to appropriate category based on overall sentiment
            if sentiment > 0.1:
                leaf = positive_node.add_leaf(node_text)
            elif sentiment < -0.1:
                leaf = negative_node.add_leaf(node_text)
            else:
                leaf = neutral_node.add_leaf(node_text)

            # Store comprehensive article data for modal display
            leaf.data = {
                "article": article,
                "sentiment": sentiment,
                "detail": detail,
                "mentioned_tickers": mentioned_tickers,
                "ticker_sentiments": detail.get("ticker_sentiments", {}),
            }

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection - update right panel with comprehensive article details"""
        if hasattr(event.node, "data") and event.node.data:
            article_data = event.node.data
            article_info = {
                "headline": article_data["article"]["headline"],
                "time_ago": article_data["article"].get("time_ago", "Unknown"),
                "sentiment": article_data["sentiment"],
                "category": article_data["detail"].get("category", "N/A"),
                "url": article_data["article"].get("url", ""),
                "mentioned_tickers": article_data.get("mentioned_tickers", []),
                "ticker_sentiments": article_data.get("ticker_sentiments", {}),
                "primary_ticker": article_data["article"].get("ticker", "N/A"),
                "text": article_data["article"].get("text", "No summary available"),
                "source": article_data["article"].get("source", "Unknown"),
            }

            # Update the right panel instead of showing a modal
            self._update_news_details_panel(article_info)

    def _update_news_details_panel(self, article_info):
        """Update the news details panel in the right pane with comprehensive article information"""
        try:
            # Find the news details panel
            news_details = self.app.query_one("#news-details", Static)

            # Store the current article URL in the dashboard for the 'o' key binding
            self.app.current_article_url = article_info.get("url", None)

            # Create comprehensive article details display
            content = self._create_article_details_content(article_info)
            news_details.update(content)

        except Exception:
            # Fallback if panel not found
            pass

    def _create_article_details_content(self, article_info):
        """Create rich content for the article details panel"""
        from rich.table import Table
        from rich.text import Text

        # Create a table for structured display
        table = Table.grid(padding=1)
        table.add_column("Field", style="bold cyan", width=18)
        table.add_column("Value", width=45)

        # Basic article information
        headline = article_info.get("headline", "N/A")
        time_ago = article_info.get("time_ago", "Unknown")
        sentiment = article_info.get("sentiment", 0)
        url = article_info.get("url", "")
        source = article_info.get("source", "Unknown")
        text = article_info.get("text", "No summary available")
        mentioned_tickers = article_info.get("mentioned_tickers", [])
        ticker_sentiments = article_info.get("ticker_sentiments", {})
        primary_ticker = article_info.get("primary_ticker", "N/A")

        # Title
        table.add_row("📰 ARTICLE DETAILS", "")
        table.add_row("", "")

        # Sentiment color coding
        if sentiment > 0.1:
            sentiment_style = "green"
            sentiment_emoji = "🟢"
        elif sentiment < -0.1:
            sentiment_style = "red"
            sentiment_emoji = "🔴"
        else:
            sentiment_style = "yellow"
            sentiment_emoji = "🟡"

        # Basic information
        table.add_row(
            "📰 Headline:", headline[:45] + "..." if len(headline) > 45 else headline
        )
        table.add_row("⏰ Published:", time_ago)
        table.add_row(
            "📊 Sentiment:",
            Text(f"{sentiment_emoji} {sentiment:.3f}", style=sentiment_style),
        )

        # Enhanced source display
        clean_source = (
            source.replace("Yahoo Finance (", "").replace(")", "")
            if "Yahoo Finance" in source
            else source
        )
        table.add_row("📡 Source:", f"Yahoo Finance - {clean_source}")

        # Associated tickers section
        table.add_row("", "")
        table.add_row("🎯 TICKERS", "")

        if mentioned_tickers and len(mentioned_tickers) > 0:
            if len(mentioned_tickers) == 1:
                # Single ticker
                ticker = mentioned_tickers[0]
                table.add_row("📈 Primary:", ticker)

                if ticker in ticker_sentiments:
                    ticker_sentiment = ticker_sentiments[ticker]
                    sentiment_cat = ticker_sentiment.get(
                        "sentiment_category", "Neutral"
                    )
                    sentiment_score = ticker_sentiment.get("sentiment_score", 0)

                    if sentiment_cat == "Positive":
                        ticker_emoji = "🟢"
                        ticker_style = "green"
                    elif sentiment_cat == "Negative":
                        ticker_emoji = "🔴"
                        ticker_style = "red"
                    else:
                        ticker_emoji = "🟡"
                        ticker_style = "yellow"

                    table.add_row(
                        "📊 Analysis:",
                        Text(
                            f"{ticker_emoji} {sentiment_cat} ({sentiment_score:+.3f})",
                            style=ticker_style,
                        ),
                    )
            else:
                # Multi-ticker article
                table.add_row(
                    "🔗 Type:", f"Multi-ticker ({len(mentioned_tickers)} tickers)"
                )

                # Show tickers with sentiments
                ticker_lines = []
                for ticker in mentioned_tickers:
                    if ticker in ticker_sentiments:
                        ticker_sentiment = ticker_sentiments[ticker]
                        sentiment_cat = ticker_sentiment.get(
                            "sentiment_category", "Neutral"
                        )
                        sentiment_score = ticker_sentiment.get("sentiment_score", 0)

                        if sentiment_cat == "Positive":
                            ticker_emoji = "🟢"
                        elif sentiment_cat == "Negative":
                            ticker_emoji = "🔴"
                        else:
                            ticker_emoji = "🟡"

                        ticker_lines.append(
                            f"{ticker_emoji} {ticker} ({sentiment_score:+.2f})"
                        )
                    else:
                        ticker_lines.append(f"⚪ {ticker} (N/A)")

                # Display tickers (max 2 per line)
                for i in range(0, len(ticker_lines), 2):
                    group = ticker_lines[i : i + 2]
                    if i == 0:
                        table.add_row("📊 Analysis:", " | ".join(group))
                    else:
                        table.add_row("", " | ".join(group))
        else:
            # Fallback to primary ticker
            table.add_row("📈 Primary:", primary_ticker)

        # Summary section
        table.add_row("", "")
        table.add_row("📝 SUMMARY", "")

        if text and text != "No summary available" and text.strip():
            # Split long summaries for better display
            if len(text) > 200:
                summary_part1 = text[:200]
                summary_part2 = text[200:400] + "..." if len(text) > 400 else text[200:]
                table.add_row("📄 Content:", summary_part1)
                if summary_part2.strip():
                    table.add_row("", summary_part2)
            else:
                table.add_row("📄 Content:", text)
        else:
            table.add_row("📄 Content:", "No summary available")

        # URL section
        if url:
            table.add_row("", "")
            table.add_row("🌐 Full Article:", "Available - press 'o' to open")

        return table


class SummaryPanel(Static):
    """Enhanced panel showing market summary (policy moved to dedicated tab)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "📊 Market Overview"

    def update_data(
        self, sentiment_analysis, policy_analysis, market_health, market_data=None
    ):
        """Update the summary panel with market data (policy analysis in separate tab)"""
        # Market sentiment
        market_mood = sentiment_analysis.get("market_mood", "N/A")
        market_score = sentiment_analysis.get("average_sentiment", 0)
        market_emoji = self._get_mood_emoji(market_score, market_mood)

        # Recommendation
        recommendation = (
            market_health.get("recommendation", "N/A") if market_health else "N/A"
        )
        market_trend = (
            market_health.get("market_trend", "Unknown") if market_health else "Unknown"
        )

        # Create enhanced summary with clear section headers
        table = Table.grid(padding=1)
        table.add_column("Section", style="bold cyan", width=22)
        table.add_column("Details", width=50)

        # MARKET SENTIMENT SECTION
        pos_pct = sentiment_analysis.get("positive_percentage", 0)
        neg_pct = sentiment_analysis.get("negative_percentage", 0)
        total_articles = sentiment_analysis.get("total_articles", 0)

        table.add_row("📊 MARKET SENTIMENT", "")
        table.add_row("", f"{market_emoji} {market_mood} ({market_score:+.3f})")
        table.add_row("", f"📈 {pos_pct:.0f}% Positive | 📉 {neg_pct:.0f}% Negative")
        table.add_row("", f"📊 {total_articles} Articles Analyzed")
        table.add_row("", "")

        # MARKET INDICES SECTION
        if market_data:
            # Create a single formatted string with all indices
            indices_lines = []
            for ticker, data in list(market_data.items())[:5]:  # Show all 5 indices
                change = data.get("price_change", 0)
                emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                # Use shorter names for better fit
                name_map = {
                    "S&P 500": "S&P 500",
                    "NASDAQ": "NASDAQ",
                    "Dow Jones": "Dow",
                    "Russell 2000": "Russell",
                    "Total Stock Market": "Total Market",
                }
                name = data.get("name", ticker)
                short_name = name_map.get(name, name)
                indices_lines.append(f"{emoji} {short_name}: {change:+.1f}%")

            # Add all indices as a single formatted entry
            indices_text = " | ".join(indices_lines)
            table.add_row("📈 MARKET INDICES", indices_text)
            table.add_row("", "")

        # TRADING RECOMMENDATION SECTION
        table.add_row("🚀 RECOMMENDATION", "")
        table.add_row("", f"Action: {recommendation}")
        table.add_row("", f"Trend: {market_trend}")
        table.add_row("", "")

        # POLICY REFERENCE
        if policy_analysis:
            policy_mood = policy_analysis.get("policy_mood", "N/A")
            policy_score = policy_analysis.get("policy_sentiment", 0)
            policy_emoji = self._get_mood_emoji(policy_score, policy_mood)
            table.add_row("🏛️ POLICY SUMMARY", "")
            table.add_row("", f"{policy_emoji} {policy_mood} ({policy_score:+.3f})")
            table.add_row("", "📋 See Policy tab for detailed analysis")

        # Update the widget content
        self.update(table)

    def _get_mood_emoji(self, sentiment_score, _mood_text):
        """Get appropriate emoji based on sentiment (standardized thresholds)"""
        if sentiment_score > 0.1:
            return "😊"
        elif sentiment_score < -0.1:
            return "😠"
        else:
            return "😐"


class NewsPanel(ScrollableContainer):
    """Panel showing recent news with multi-ticker information"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "📰 Recent Market News"

    def update_data(
        self, news_data, sentiment_scores, sentiment_details, multi_ticker_articles
    ):
        """Update the news panel with new data"""
        # Clear existing content
        self.remove_children()

        # Create a mapping of articles to their multi-ticker data
        multi_ticker_map = {}
        for mt_article in multi_ticker_articles:
            article_index = mt_article["article_index"]
            multi_ticker_map[article_index] = mt_article

        # Combine and sort by recency
        combined_data = []
        for i, article in enumerate(news_data[:30]):
            if i < len(sentiment_scores):
                combined_data.append(
                    {
                        "article": article,
                        "sentiment_score": sentiment_scores[i],
                        "article_index": i,
                        "sentiment_detail": (
                            sentiment_details[i] if i < len(sentiment_details) else {}
                        ),
                    }
                )

        combined_data.sort(key=lambda x: x["article"].get("datetime", ""), reverse=True)

        # Add news items
        for i, item in enumerate(combined_data[:20], 1):
            article = item["article"]
            sentiment_score = item["sentiment_score"]
            article_index = item["article_index"]
            sentiment_detail = item["sentiment_detail"]

            # Create news item widget
            news_item = self._create_news_item(
                i,
                article,
                sentiment_score,
                article_index,
                multi_ticker_map,
                sentiment_detail,
            )
            self.mount(news_item)

    def _create_news_item(
        self,
        index,
        article,
        sentiment_score,
        article_index,
        multi_ticker_map,
        sentiment_detail,
    ):
        """Create a single news item widget"""
        # Sentiment emoji
        if sentiment_score > 0.1:
            emoji = "🟢"
        elif sentiment_score > -0.1:
            emoji = "🟡"
        else:
            emoji = "🔴"

        # Get ticker information
        primary_ticker = article.get("ticker", "N/A")
        time_info = article.get("time_ago", "Unknown")
        headline = article["headline"]

        # Check for multi-ticker information
        mentioned_tickers = []
        ticker_sentiments = {}

        if article_index in multi_ticker_map:
            mt_data = multi_ticker_map[article_index]
            mentioned_tickers = mt_data["mentioned_tickers"]
            ticker_sentiments = mt_data["ticker_sentiments"]
        elif "mentioned_tickers" in sentiment_detail:
            mentioned_tickers = sentiment_detail["mentioned_tickers"]
            ticker_sentiments = sentiment_detail.get("ticker_sentiments", {})

        # Create content - escape markup characters
        content_lines = []
        # Escape square brackets to prevent markup interpretation
        safe_time_info = time_info.replace("[", "\\[").replace("]", "\\]")
        safe_headline = headline.replace("[", "\\[").replace("]", "\\]")

        content_lines.append(f"{index:2d}. {emoji} \\[{safe_time_info}\\]")
        content_lines.append(f"    {safe_headline}")

        # Show tickers
        if len(mentioned_tickers) > 1:
            # Multi-ticker article
            ticker_parts = []
            for ticker in mentioned_tickers[:4]:
                if ticker in ticker_sentiments:
                    ticker_sentiment = ticker_sentiments[ticker]
                    if ticker_sentiment["sentiment_category"] == "Positive":
                        ticker_emoji = "🟢"
                    elif ticker_sentiment["sentiment_category"] == "Negative":
                        ticker_emoji = "🔴"
                    else:
                        ticker_emoji = "🟡"
                    ticker_parts.append(f"{ticker_emoji}{ticker}")
                else:
                    ticker_parts.append(f"⚪{ticker}")

            if len(mentioned_tickers) > 4:
                ticker_parts.append(f"+{len(mentioned_tickers)-4}")

            content_lines.append(f"    🔗 {' '.join(ticker_parts)}")
        else:
            content_lines.append(f"    📊 {primary_ticker}")

        return Static("\n".join(content_lines), classes="news-item", markup=False)


class TickersPanel(Static):
    """Enhanced panel showing top performing tickers with detailed metrics"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "🏆 Top Sentiment Performers"

    def update_data(
        self, _sector_rankings, ticker_rankings, price_changes, current_prices
    ):
        """Update the tickers panel with new data"""
        table = Table()
        table.add_column("Rank", style="bold cyan", width=4)
        table.add_column("Ticker", style="bold", width=8)
        table.add_column("Price & Change", width=18)
        table.add_column("Sentiment", width=10)

        # Add header row
        table.title = "Top 6 Tickers by Sentiment Score"

        # Add top tickers
        for i, ticker in enumerate(ticker_rankings[:6], 1):
            ticker_symbol = ticker["ticker"]
            price_change = price_changes.get(ticker_symbol, 0.0)
            current_price = (
                current_prices.get(ticker_symbol) if current_prices else None
            )

            # Price display with emoji
            price_emoji = (
                "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
            )
            price_str = f"${current_price:.2f}" if current_price else "N/A"
            price_display = f"{price_emoji} {price_str} ({price_change:+.1f}%)"

            # Sentiment score with color (standardized thresholds)
            sentiment_score = ticker["overall_score"]
            if sentiment_score > 0.1:
                sentiment_style = "green"
            elif sentiment_score < -0.1:
                sentiment_style = "red"
            else:
                sentiment_style = "yellow"

            table.add_row(
                f"{i}",
                ticker_symbol,
                price_display,
                Text(f"{sentiment_score:.3f}", style=sentiment_style),
            )

        self.update(table)


class SectorsPanel(Static):
    """Enhanced panel showing top performing sectors with detailed metrics"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "🏭 Sector Performance Rankings"

    def update_data(self, sector_rankings, price_changes):
        """Update the sectors panel with new data"""
        if not sector_rankings:
            self.update("No sector data available")
            return

        table = Table()
        table.add_column("Rank", style="bold cyan", width=4)
        table.add_column("Sector", width=14)
        table.add_column("Strength", width=8)
        table.add_column("Top Ticker", width=12)

        table.title = "Top 5 Sectors by Sentiment Strength"

        # Add top sectors
        for i, sector in enumerate(sector_rankings[:5], 1):
            # Sector sentiment emoji (standardized thresholds)
            avg_sentiment = sector["average_sentiment"]
            if avg_sentiment > 0.1:
                emoji = "🟢"
                sentiment_style = "green"
            elif avg_sentiment < -0.1:
                emoji = "🔴"
                sentiment_style = "red"
            else:
                emoji = "🟡"
                sentiment_style = "yellow"

            # Top ticker info
            top_ticker = sector["top_ticker"]
            price_change = price_changes.get(top_ticker, 0.0)
            price_emoji = (
                "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
            )

            table.add_row(
                f"{i}",
                f"{emoji} {sector['sector'][:12]}",
                Text(f"{sector['sector_strength']:.2f}", style=sentiment_style),
                f"{price_emoji} {top_ticker}",
            )

        self.update(table)


class MultiTickerPanel(Static):
    """Enhanced panel showing multi-ticker analysis with clear metrics"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "🔄 Cross-Ticker Analysis"

    def update_data(self, multi_ticker_articles, cross_ticker_analysis):
        """Update the multi-ticker panel with new data"""
        if not multi_ticker_articles:
            self.update("No multi-ticker articles found")
            return

        # Create structured table
        table = Table.grid(padding=1)
        table.add_column("Metric", style="bold cyan", width=18)
        table.add_column("Value", width=30)

        # Summary metrics
        conflicts_count = len(cross_ticker_analysis.get("sentiment_conflicts", []))
        pairs_count = len(cross_ticker_analysis.get("ticker_pairs", {}))

        table.add_row("📊 ANALYSIS SUMMARY", "")
        table.add_row("", f"Multi-ticker Articles: {len(multi_ticker_articles)}")
        table.add_row("", f"Sentiment Conflicts: {conflicts_count}")
        table.add_row("", f"Ticker Pairs Found: {pairs_count}")
        table.add_row("", "")

        # Show top conflicts
        if cross_ticker_analysis.get("sentiment_conflicts"):
            table.add_row("⚠️ TOP CONFLICTS", "")
            for i, conflict in enumerate(
                cross_ticker_analysis["sentiment_conflicts"][:3], 1
            ):
                pos_tickers = ", ".join(conflict["positive_tickers"][:2])
                neg_tickers = ", ".join(conflict["negative_tickers"][:2])
                table.add_row("", f"{i}. 🟢 {pos_tickers} vs 🔴 {neg_tickers}")

        self.update(table)


class PolicySummaryPanel(Static):
    """Comprehensive policy analysis summary panel"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "🏛️ Government Policy Analysis"

    def update_data(self, policy_analysis):
        """Update the policy summary panel with comprehensive data"""
        if not policy_analysis:
            self.update("No policy data available")
            return

        # Create comprehensive policy summary
        table = Table.grid(padding=1)
        table.add_column("Section", style="bold cyan", width=25)
        table.add_column("Details", width=60)

        # Policy sentiment overview
        policy_mood = policy_analysis.get("policy_mood", "No Data")
        policy_sentiment = policy_analysis.get("policy_sentiment", 0)
        policy_emoji = self._get_policy_emoji(policy_sentiment, policy_mood)

        table.add_row("📊 POLICY SENTIMENT", "")
        table.add_row("", f"{policy_emoji} {policy_mood} ({policy_sentiment:+.3f})")
        table.add_row("", "")

        # Article statistics
        total_articles = policy_analysis.get("total_policy_articles", 0)
        high_impact_count = len(policy_analysis.get("high_impact_articles", []))

        table.add_row("📄 ARTICLE ANALYSIS", "")
        table.add_row("", f"Total Policy Articles: {total_articles}")
        table.add_row("", f"High Impact Articles: {high_impact_count}")
        table.add_row(
            "",
            f"Impact Rate: {(high_impact_count/total_articles*100) if total_articles > 0 else 0:.1f}%",
        )
        table.add_row("", "")

        # Policy categories if available
        if "policy_categories" in policy_analysis:
            table.add_row("🏷️ POLICY CATEGORIES", "")
            categories = policy_analysis["policy_categories"]
            for category, count in list(categories.items())[:5]:
                table.add_row("", f"{category}: {count} articles")
            table.add_row("", "")

        # Market impact assessment
        market_impact = policy_analysis.get("market_impact_score", 0)
        if market_impact != 0:
            impact_emoji = (
                "📈" if market_impact > 0 else "📉" if market_impact < 0 else "➡️"
            )
            table.add_row("💼 MARKET IMPACT", "")
            table.add_row("", f"{impact_emoji} Impact Score: {market_impact:+.3f}")
            table.add_row(
                "", f"Assessment: {self._get_impact_assessment(market_impact)}"
            )

        self.update(table)

    def _get_policy_emoji(self, sentiment_score, _mood_text):
        """Get appropriate emoji for policy sentiment"""
        if sentiment_score > 0.1:
            return "🟢"
        elif sentiment_score > 0:
            return "🟡"
        elif sentiment_score < -0.1:
            return "🔴"
        else:
            return "⚪"

    def _get_impact_assessment(self, impact_score):
        """Get market impact assessment text"""
        if impact_score > 0.2:
            return "Strongly Positive"
        elif impact_score > 0.05:
            return "Moderately Positive"
        elif impact_score > -0.05:
            return "Neutral"
        elif impact_score > -0.2:
            return "Moderately Negative"
        else:
            return "Strongly Negative"


class PolicyTreeView(Tree):
    """Tree view for policy articles organized by sentiment, similar to NewsTreeView"""

    def __init__(self, **kwargs):
        super().__init__("🏛️ Policy Articles", **kwargs)
        self.border_title = "🏛️ Government Policy Articles"
        self.show_root = False

    def update_data(self, policy_analysis):
        """Update the tree with policy articles organized by sentiment"""
        # Clear existing tree
        self.clear()

        if not policy_analysis:
            return

        # Create sentiment category nodes
        positive_node = self.root.add("🟢 Positive Policy News", expand=True)
        neutral_node = self.root.add("🟡 Neutral Policy News", expand=True)
        negative_node = self.root.add("🔴 Negative Policy News", expand=True)

        # Get policy articles from different possible sources
        policy_articles = []

        # Check for high impact articles first
        if "high_impact_articles" in policy_analysis:
            policy_articles.extend(policy_analysis["high_impact_articles"])

        # Check for general articles
        if "articles" in policy_analysis:
            policy_articles.extend(policy_analysis["articles"])

        # If no articles found, create some sample policy articles for demonstration
        if not policy_articles:
            sample_articles = [
                {
                    "headline": "Federal Reserve Announces New Interest Rate Policy",
                    "sentiment": 0.2,
                    "time_ago": "2 hours ago",
                    "category": "Monetary Policy",
                    "url": "https://example.com/fed-policy",
                    "impact_score": 0.8,
                    "policy_type": "monetary_policy",
                },
                {
                    "headline": "New Banking Regulations Proposed by Treasury",
                    "sentiment": -0.1,
                    "time_ago": "4 hours ago",
                    "category": "Regulatory",
                    "url": "https://example.com/banking-regs",
                    "impact_score": 0.6,
                    "policy_type": "regulatory",
                },
                {
                    "headline": "Trade Policy Updates Announced",
                    "sentiment": 0.05,
                    "time_ago": "6 hours ago",
                    "category": "Trade Policy",
                    "url": "https://example.com/trade-policy",
                    "impact_score": 0.4,
                    "policy_type": "trade",
                },
            ]
            policy_articles = sample_articles

        for article in policy_articles:
            headline = article.get("headline", "No headline")
            if len(headline) > 100:
                headline = headline[:97] + "..."

            # Get sentiment score
            sentiment = article.get("sentiment", 0)
            time_ago = article.get("time_ago", "Unknown")
            category = article.get("category", "Policy")

            # Create node text with metadata
            node_text = f"[{time_ago}] {category}: {headline}"

            # Add to appropriate category based on sentiment
            if sentiment > 0.1:
                leaf = positive_node.add_leaf(node_text)
            elif sentiment < -0.1:
                leaf = negative_node.add_leaf(node_text)
            else:
                leaf = neutral_node.add_leaf(node_text)

            # Store article data for modal display
            leaf.data = {
                "article": article,
                "sentiment": sentiment,
                "category": category,
            }

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection - show policy article details"""
        if hasattr(event.node, "data") and event.node.data:
            article_data = event.node.data
            article_info = {
                "headline": article_data["article"]["headline"],
                "time_ago": article_data["article"].get("time_ago", "Unknown"),
                "sentiment": article_data["sentiment"],
                "category": article_data["category"],
                "url": article_data["article"].get("url", ""),
                "impact_score": article_data["article"].get("impact_score", 0),
                "policy_type": article_data["article"].get("policy_type", "General"),
                "summary": article_data["article"].get(
                    "summary", "No summary available"
                ),
            }
            self.app.push_screen(PolicyArticleDetailModal(article_info))


class PolicyArticleDetailModal(ModalScreen):
    """Enhanced modal screen showing detailed policy article analysis"""

    def __init__(self, article_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.article_data = article_data

    def compose(self) -> ComposeResult:
        with Container(id="article-modal"):
            yield Label("🏛️ Policy Article Details", id="modal-title")

            # Create rich article content with proper formatting
            table = Table.grid(padding=1)
            table.add_column("Field", style="bold cyan", width=15)
            table.add_column("Value", width=60)

            # Article details
            headline = self.article_data.get("headline", "N/A")
            time_ago = self.article_data.get("time_ago", "Unknown")
            sentiment = self.article_data.get("sentiment", 0)
            category = self.article_data.get("category", "N/A")
            policy_type = self.article_data.get("policy_type", "General")
            impact_score = self.article_data.get("impact_score", 0)
            url = self.article_data.get("url", "")
            summary = self.article_data.get("summary", "No summary available")

            # Sentiment color coding
            if sentiment > 0.1:
                sentiment_style = "green"
                sentiment_emoji = "🟢"
            elif sentiment < -0.1:
                sentiment_style = "red"
                sentiment_emoji = "🔴"
            else:
                sentiment_style = "yellow"
                sentiment_emoji = "🟡"

            # Impact level emoji
            if impact_score > 0.7:
                impact_emoji = "🔥"
            elif impact_score > 0.5:
                impact_emoji = "⚡"
            elif impact_score > 0.3:
                impact_emoji = "📢"
            else:
                impact_emoji = "📄"

            table.add_row(
                "📰 Headline:",
                headline[:50] + "..." if len(headline) > 50 else headline,
            )
            table.add_row("⏰ Time:", time_ago)
            table.add_row("🏷️ Category:", category)
            table.add_row("🏛️ Policy Type:", policy_type)
            table.add_row(
                "📊 Sentiment:",
                Text(f"{sentiment_emoji} {sentiment:.3f}", style=sentiment_style),
            )
            table.add_row(
                "⚡ Impact:", Text(f"{impact_emoji} {impact_score:.2f}", style="bold")
            )

            # Summary
            if summary and summary != "No summary available":
                summary_text = summary[:100] + "..." if len(summary) > 100 else summary
                table.add_row("📝 Summary:", summary_text)

            # URL with hyperlink if available
            if url:
                # Create clickable hyperlink using OSC 8 escape sequences
                hyperlink = f"\033]8;;{url}\033\\🔗 Click to open article\033]8;;\033\\"
                table.add_row("🌐 Link:", hyperlink)
            else:
                table.add_row("🌐 Link:", "Not available")

            yield Static(table, id="article-content")

            with Horizontal():
                yield Button("Close", variant="primary", id="close-modal")
                if url:
                    yield Button("🌐 Open URL", variant="success", id="open-url")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-modal":
            self.dismiss()
        elif event.button.id == "open-url":
            url = self.article_data.get("url", "")
            if url:
                # Open URL in default browser
                import webbrowser

                try:
                    webbrowser.open(url)
                    self.app.notify(
                        "Opening policy article in browser...", severity="information"
                    )
                except Exception as e:
                    self.app.notify(f"Could not open URL: {str(e)}", severity="error")
            self.dismiss()


class PolicyTimelinePanel(Static):
    """Panel showing policy timeline and trends"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "📈 Policy Sentiment Timeline"

    def update_data(self, policy_analysis):
        """Update with policy timeline data"""
        if not policy_analysis:
            self.update("No policy timeline data available")
            return

        # Create timeline visualization
        content_lines = []
        content_lines.append("📊 POLICY SENTIMENT TRENDS")
        content_lines.append("")

        # Current sentiment
        current_sentiment = policy_analysis.get("policy_sentiment", 0)
        trend_emoji = (
            "📈" if current_sentiment > 0 else "📉" if current_sentiment < 0 else "➡️"
        )
        content_lines.append(f"Current Trend: {trend_emoji} {current_sentiment:+.3f}")
        content_lines.append("")

        # Recent policy changes if available
        if "recent_changes" in policy_analysis:
            content_lines.append("🔄 RECENT POLICY CHANGES:")
            for change in policy_analysis["recent_changes"][:5]:
                change_emoji = (
                    "🟢"
                    if change.get("impact", 0) > 0
                    else "🔴" if change.get("impact", 0) < 0 else "🟡"
                )
                content_lines.append(
                    f"  {change_emoji} {change.get('description', 'Policy change')}"
                )
            content_lines.append("")

        # Policy sectors affected
        if "affected_sectors" in policy_analysis:
            content_lines.append("🏭 AFFECTED SECTORS:")
            sectors = policy_analysis["affected_sectors"]
            for sector, impact in list(sectors.items())[:5]:
                sector_emoji = "📈" if impact > 0 else "📉" if impact < 0 else "➡️"
                content_lines.append(f"  {sector_emoji} {sector}: {impact:+.2f}")

        self.update("\n".join(content_lines))


class MarketIndexCard(Static):
    """Individual market index card with collapsible chart"""

    def __init__(self, index_ticker: str, index_name: str, **kwargs):
        super().__init__(**kwargs)
        self.index_ticker = index_ticker
        self.index_name = index_name
        self.border_title = f"📈 {index_name} ({index_ticker})"

    def compose(self) -> ComposeResult:
        with Collapsible(
            title=f"📊 {self.index_name} ({self.index_ticker})", collapsed=True
        ):
            # Basic info section
            yield Static("Loading index data...", id=f"info-{self.index_ticker}")
            # Chart section
            yield PlotextPlot(id=f"chart-{self.index_ticker}", classes="index-chart")

    def update_data(self, market_data: Dict, historical_data: Dict = None):
        """Update the index card with current and historical data"""
        try:
            # Update basic info
            info_widget = self.query_one(f"#info-{self.index_ticker}", Static)

            if self.index_ticker in market_data:
                index_info = market_data[self.index_ticker]
                price_change = index_info.get("price_change", 0)
                current_price = index_info.get("current_price", "N/A")

                # Create info display
                info_table = Table.grid(padding=1)
                info_table.add_column("Metric", style="bold cyan", width=15)
                info_table.add_column("Value", width=25)

                # Price change with color coding
                if price_change > 0:
                    change_style = "green"
                    change_emoji = "📈"
                elif price_change < 0:
                    change_style = "red"
                    change_emoji = "📉"
                else:
                    change_style = "yellow"
                    change_emoji = "➡️"

                info_table.add_row("📊 Index:", self.index_name)
                info_table.add_row("🎯 Symbol:", self.index_ticker)
                if current_price != "N/A":
                    info_table.add_row("💰 Price:", f"${current_price:.2f}")
                info_table.add_row(
                    "📈 Change:",
                    Text(f"{change_emoji} {price_change:+.2f}%", style=change_style),
                )

                # Performance assessment
                if abs(price_change) > 2:
                    performance = "High Volatility"
                    perf_style = "red"
                elif abs(price_change) > 1:
                    performance = "Moderate Movement"
                    perf_style = "yellow"
                else:
                    performance = "Stable"
                    perf_style = "green"

                info_table.add_row("📊 Status:", Text(performance, style=perf_style))

                info_widget.update(info_table)
            else:
                info_widget.update("No data available for this index")

            # Update chart
            self._update_chart(historical_data)

        except Exception:
            # Fallback if widgets not found
            pass

    def _update_chart(self, historical_data: Dict = None):
        """Update the chart with 6-month historical data"""
        try:
            chart_widget = self.query_one(f"#chart-{self.index_ticker}", PlotextPlot)

            if historical_data and self.index_ticker in historical_data:
                prices, dates = historical_data[self.index_ticker]

                if len(prices) < 2:
                    chart_widget.plt.clear_data()
                    chart_widget.plt.clear_figure()
                    chart_widget.plt.text(
                        0.5, 0.5, "No historical data available", alignment="center"
                    )
                    chart_widget.plt.title(f"{self.index_ticker} - No Data")
                    return

                # Clear previous plot
                chart_widget.plt.clear_data()
                chart_widget.plt.clear_figure()

                # Use 6 months of data (approximately 130 trading days)
                chart_prices = prices[-130:] if len(prices) >= 130 else prices
                chart_dates_raw = dates[-130:] if dates and len(dates) >= 130 else dates

                # Convert dates to strings for x-axis labels
                if chart_dates_raw:
                    # Format dates as MM/DD for better readability
                    date_labels = []
                    for date in chart_dates_raw:
                        if hasattr(date, "strftime"):
                            date_labels.append(date.strftime("%m/%d"))
                        else:
                            date_labels.append(str(date))

                    # Use numeric sequence for plotting
                    chart_x_values = list(range(len(chart_prices)))

                    # Create the plot with enhanced styling for wider charts
                    chart_widget.plt.plot(
                        chart_x_values,
                        chart_prices,
                        marker="braille",
                        color="cyan",
                        fillx=True,
                    )

                    # Set custom x-axis labels for wider charts - show more labels
                    step = max(
                        1, len(date_labels) // 12
                    )  # Show about 12 labels for wider view
                    x_ticks = list(range(0, len(date_labels), step))
                    x_labels = [date_labels[i] for i in x_ticks]

                    chart_widget.plt.xticks(x_ticks, x_labels)

                    # Set chart dimensions for better visibility
                    chart_widget.plt.plotsize(80, 12)  # Wider plot for better detail
                else:
                    # Fallback to numeric sequence if no dates
                    chart_x_values = list(range(len(chart_prices)))
                    chart_widget.plt.plot(
                        chart_x_values,
                        chart_prices,
                        marker="braille",
                        color="cyan",
                        fillx=True,
                    )
                    chart_widget.plt.plotsize(80, 12)  # Consistent sizing

                # Configure the plot with enhanced styling
                chart_widget.plt.title(f"{self.index_ticker} - 6 Month History")
                chart_widget.plt.xlabel("Date")
                chart_widget.plt.ylabel("Price ($)")

                # Add grid for better readability
                chart_widget.plt.grid(True, True)

                # Show price range in title for context
                min_price = min(chart_prices)
                max_price = max(chart_prices)
                price_range = f"Range: ${min_price:.2f} - ${max_price:.2f}"
                chart_widget.plt.title(
                    f"{self.index_ticker} - 6 Month History | {price_range}"
                )

            else:
                # No data available
                chart_widget.plt.clear_data()
                chart_widget.plt.clear_figure()
                chart_widget.plt.text(
                    0.5, 0.5, "Loading historical data...", alignment="center"
                )
                chart_widget.plt.title(f"{self.index_ticker} - Loading...")

        except Exception:
            # Fallback if chart widget not found
            pass


class MarketIndicesPanel(ScrollableContainer):
    """Panel containing all market index cards"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "📈 Market Indices Overview"
        self.index_cards = {}

    def compose(self) -> ComposeResult:
        # Import here to avoid circular imports
        from ..config.config import MARKET_INDICES

        # Create cards for each market index
        for ticker, name in MARKET_INDICES.items():
            card = MarketIndexCard(ticker, name, id=f"card-{ticker}")
            self.index_cards[ticker] = card
            yield card

    def update_data(self, market_data: Dict, historical_data: Dict = None):
        """Update all index cards with current and historical data"""
        for _ticker, card in self.index_cards.items():
            card.update_data(market_data, historical_data)


class StockholmDashboard(App):
    """Stockholm - Enhanced Interactive Dashboard with Tabbed Interface"""

    CSS = """
    #ticker-modal, #article-modal {
        align: center middle;
        width: 80;
        height: 20;
        background: $surface;
        border: thick $primary;
    }

    #modal-title {
        dock: top;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $primary;
        color: $text;
    }

    #article-content {
        padding: 1;
        height: 1fr;
    }

    .data-table {
        height: 1fr;
    }

    .chart-container {
        height: 8;
        border: solid $primary;
        margin: 1;
    }

    .controls-panel {
        height: 6;
        border: solid $secondary;
        margin: 1;
    }

    .status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
    }

    TabbedContent {
        height: 1fr;
    }

    TabPane {
        padding: 1;
    }

    .news-item {
        margin: 1;
        padding: 1;
    }

    #left-panel {
        width: 1fr;
        margin: 1;
    }

    #right-panel {
        width: 2fr;
        margin: 1;
    }

    #summary-panel {
        height: 16;
        margin: 1;
        border: solid $primary;
    }

    #tickers-panel {
        height: 1fr;
        margin: 1;
        border: solid $secondary;
        width: 1fr;
    }

    #sectors-panel {
        height: 1fr;
        margin: 1;
        border: solid $secondary;
        width: 1fr;
    }

    #multi-ticker-panel {
        height: 1fr;
        margin: 1;
        border: solid $secondary;
        width: 1fr;
    }

    .details-panel {
        height: 1fr;
        margin: 1;
        border: solid $primary;
        padding: 1;
        width: 1fr;
    }

    #ticker-panels-row {
        height: 15;
        margin: 1;
    }

    .info-panel {
        width: 1fr;
        height: 100%;
        scrollbar-gutter: stable;
        overflow-y: auto;
        margin-right: 1;
        border: solid $primary;
        padding: 1;
    }

    .earnings-panel {
        width: 1fr;
        height: 100%;
        scrollbar-gutter: stable;
        overflow-y: auto;
        margin-left: 1;
        border: solid $secondary;
        padding: 1;
    }

    #ticker-chart {
        height: 1fr;
        border: solid $primary;
        margin: 1;
    }

    .chart-widget {
        height: 15;
        width: 1fr;
        min-width: 80;
        border: solid $primary;
        margin: 1;
        background: $surface;
    }

    .index-chart {
        height: 15;
        width: 1fr;
        min-width: 80;
        border: solid $primary;
        margin: 1;
        background: $surface;
    }

    #market-indices-panel {
        height: 1fr;
        padding: 1;
    }

    MarketIndexCard {
        margin: 1;
        border: solid $secondary;
        height: auto;
        width: 1fr;
        min-width: 90;
    }

    #ticker-details-container {
        width: 2fr;
        height: 1fr;
    }

    #ticker-news-panel {
        height: 1fr;
        padding: 1;
        border: solid $secondary;
    }

    #ticker-news-content {
        height: 1fr;
        scrollbar-gutter: stable;
        overflow-y: auto;
    }

    #ticker-news-table {
        height: 1fr;
        border: solid $secondary;
    }

    .news-table-panel {
        height: 60%;
        border: solid $secondary;
        margin-bottom: 1;
    }

    .timeline-chart-panel {
        height: 40%;
        border: solid $secondary;
    }

    #news-table-container {
        height: 1fr;
        scrollbar-gutter: stable;
        overflow-y: auto;
    }

    #article-timeline-chart {
        height: 1fr;
    }

    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "toggle_filter", "Toggle Filters"),
        Binding("1", "switch_tab('overview')", "Overview"),
        Binding("2", "switch_tab('tickers')", "Tickers"),
        Binding("3", "switch_tab('news')", "News"),
        Binding("4", "switch_tab('policy')", "Policy"),
        Binding("5", "switch_tab('indices')", "Indices"),
        Binding("o", "open_article_url", "Open Article URL"),
        Binding("ctrl+e", "export_data", "Export"),
    ]

    TITLE = "🦍🦍💪💪 Stockholm - Interactive Real-time Market Analysis 💎🙌🚀🌙"
    SUB_TITLE = ""

    # Reactive variables for data
    current_sentiment = var(0.0)
    last_update = var("")
    auto_refresh_enabled = var(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_cache = {}
        self.quick_mode = False
        self.verbose_mode = False
        self.current_article_url = None  # Store current article URL for opening
        self.background_fetcher = None  # Will be initialized in on_mount

    def compose(self) -> ComposeResult:
        """Create the enhanced dashboard layout"""
        yield Header()

        with TabbedContent(initial="overview"):
            # Overview Tab - Enhanced summary dashboard
            with TabPane("📊 Overview", id="overview"):
                with Vertical():
                    # Top row - Market summary
                    yield SummaryPanel(id="summary-panel")

                    # Bottom row - Performance metrics in columns
                    with Horizontal():
                        yield TickersPanel(id="tickers-panel")
                        yield SectorsPanel(id="sectors-panel")
                        yield MultiTickerPanel(id="multi-ticker-panel")

            # Interactive Tickers Tab with Right Panel
            with TabPane("🏆 Tickers", id="tickers"):
                with Vertical():
                    yield FilterControls(classes="controls-panel")
                    with Horizontal():
                        # Left side - Ticker table
                        with Vertical():
                            yield InteractiveTickerTable(classes="data-table")
                        # Right side - Tabbed ticker details
                        with Vertical(id="ticker-details-container"):
                            with TabbedContent(initial="details"):
                                # Details Tab - Info, Earnings, and Chart
                                with TabPane("📊 Details", id="details"):
                                    with Vertical():
                                        # Side-by-side panels for ticker info and earnings
                                        with Horizontal(id="ticker-panels-row"):
                                            yield Static(
                                                "📊 Select a ticker to view detailed information",
                                                id="ticker-info",
                                                classes="info-panel",
                                            )
                                            yield Static(
                                                "📊 Earnings data will appear here",
                                                id="ticker-earnings",
                                                classes="earnings-panel",
                                            )
                                        # Chart underneath the panels
                                        yield PlotextPlot(
                                            id="ticker-chart", classes="chart-widget"
                                        )

                                # News Tab - Ticker-specific news articles
                                with TabPane("📰 News", id="ticker-news"):
                                    yield TickerNewsPanel(id="ticker-news-panel")

            # News Tree Tab
            with TabPane("📰 News", id="news"):
                with Horizontal():
                    with Vertical(id="left-panel"):
                        yield NewsTreeView(id="news-tree")
                    with Vertical(id="right-panel"):
                        yield RealTimeChart(classes="chart-container")
                        with ScrollableContainer():
                            yield Static(
                                "Select an article from the tree to view details",
                                id="news-details",
                            )

            # Policy Analysis Tab
            with TabPane("🏛️ Policy", id="policy"):
                with Horizontal():
                    with Vertical():
                        yield PolicyTreeView(id="policy-tree")
                    with Vertical():
                        yield PolicySummaryPanel(id="policy-summary-panel")
                        yield PolicyTimelinePanel(id="policy-timeline-panel")

            # Market Indices Tab
            with TabPane("📈 Indices", id="indices"):
                yield MarketIndicesPanel(id="market-indices-panel")

        yield Static(
            "🔄 Auto-refresh: ON | Last update: Never",
            classes="status-bar",
            id="status-bar",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the dashboard with progressive data loading"""
        # Show dashboard immediately with loading states
        self.update_status("🚀 Dashboard ready - Loading data...")

        # Initialize background fetcher
        from ..data.cached_data_fetcher import background_fetcher

        self.background_fetcher = background_fetcher

        # Add callback for background data updates
        self.background_fetcher.add_update_callback(self.on_background_data_update)

        # Start background data fetching
        quick_mode = getattr(self, "quick_mode", False)
        self.background_fetcher.start_background_fetching(quick_mode)

        # Set up auto-refresh interval (reduced frequency since background fetcher handles updates)
        self.set_interval(
            300, self.update_dashboard_data
        )  # Every 5 minutes instead of 1

        # Start progressive data loading immediately
        self.call_later(self.start_progressive_loading)

    async def start_progressive_loading(self) -> None:
        """Start progressive data loading for better user experience"""
        try:
            # Show dashboard immediately with loading placeholders
            self.update_status("🚀 Dashboard ready - Loading data in background...")
            self.show_loading_placeholders()

            # Phase 1: Load critical data first (prices, basic market data) - NON-BLOCKING
            self.call_later(self.load_critical_data_background)

        except Exception as e:
            self.notify(f"Error during progressive loading: {str(e)}", severity="error")
            self.update_status(f"❌ Loading error: {str(e)}")

    def show_loading_placeholders(self) -> None:
        """Show the dashboard with loading placeholders immediately"""
        try:
            # Initialize empty data cache with loading indicators
            self.data_cache = {
                "loading_phase": "initializing",
                "price_changes": {},
                "current_prices": {},
                "company_names": {},
                "market_data": {},
                "news_data": [],
                "sentiment_analysis": {
                    "market_mood": "Loading...",
                    "average_sentiment": 0.0,
                },
                "ticker_rankings": [],
                "sector_rankings": [],
            }

            # Update basic panels with loading states
            self.update_basic_panels()

        except Exception:
            pass  # Fail silently to avoid blocking UI

    def load_critical_data_background(self) -> None:
        """Load critical data in background without blocking UI"""
        try:
            self.update_status("📊 Loading market prices...")

            # Run in background thread to avoid blocking UI
            import threading

            thread = threading.Thread(
                target=self._fetch_critical_data_thread, daemon=True
            )
            thread.start()

        except Exception as e:
            self.update_status(f"⚠️ Background loading error: {str(e)}")

    def _fetch_critical_data_thread(self) -> None:
        """Background thread for fetching critical data with streaming ticker updates"""
        try:
            from ..data.cached_data_fetcher import cached_get_market_data_optimized
            from ..data.data_fetcher import MAJOR_TICKERS

            # Get basic ticker data quickly
            quick_mode = getattr(self, "quick_mode", False)
            tickers = MAJOR_TICKERS[:15] if quick_mode else MAJOR_TICKERS[:30]

            # Load market data first (fastest)
            market_data = cached_get_market_data_optimized()
            self.data_cache.update({"market_data": market_data})
            self.call_later(self.update_basic_panels)

            # Initialize ticker data containers
            if "price_changes" not in self.data_cache:
                self.data_cache["price_changes"] = {}
            if "current_prices" not in self.data_cache:
                self.data_cache["current_prices"] = {}
            if "company_names" not in self.data_cache:
                self.data_cache["company_names"] = {}

            # Start streaming ticker data processing
            self.call_later(
                lambda: self.update_status("📊 Loading tickers (streaming)...")
            )
            self._stream_ticker_data(tickers)

            # Mark critical phase complete
            self.data_cache["loading_phase"] = "critical_loaded"
            self.call_later(lambda: self.update_status("📰 Loading news data..."))

            # Start next phase
            self.call_later(self.load_secondary_data_background)

        except Exception as e:
            error_msg = str(e)
            self.call_later(
                lambda: self.update_status(f"⚠️ Critical data error: {error_msg}")
            )

    def _stream_ticker_data(self, tickers):
        """Stream ticker data processing with chunked updates for responsiveness"""
        import threading
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from ..data.cached_data_fetcher import (
            cached_get_ticker_price_change,
            cached_get_ticker_current_price,
            cached_get_ticker_company_name,
        )

        def fetch_single_ticker(ticker):
            """Fetch data for a single ticker"""
            try:
                price_change = cached_get_ticker_price_change(ticker)
                current_price = cached_get_ticker_current_price(ticker)
                company_name = cached_get_ticker_company_name(ticker)

                return {
                    "ticker": ticker,
                    "price_change": price_change,
                    "current_price": current_price,
                    "company_name": company_name,
                    "success": True,
                }
            except Exception as e:
                return {
                    "ticker": ticker,
                    "price_change": 0.0,
                    "current_price": 0.0,
                    "company_name": ticker,
                    "success": False,
                    "error": str(e),
                }

        def chunked_stream_worker():
            """Worker thread for chunked streaming ticker updates"""
            completed_count = 0
            chunk_size = 5  # Process 5 tickers at a time for responsiveness
            ui_update_interval = 0.1  # Update UI every 100ms to keep it responsive

            # Process tickers in chunks to avoid overwhelming the UI
            for i in range(0, len(tickers), chunk_size):
                chunk = tickers[i : i + chunk_size]

                # Process this chunk in parallel
                with ThreadPoolExecutor(max_workers=3) as executor:
                    # Submit chunk tasks
                    future_to_ticker = {
                        executor.submit(fetch_single_ticker, ticker): ticker
                        for ticker in chunk
                    }

                    # Process chunk results
                    chunk_results = []
                    for future in as_completed(future_to_ticker):
                        try:
                            result = future.result()
                            chunk_results.append(result)
                        except Exception:
                            pass

                    # Batch update cache with chunk results
                    for result in chunk_results:
                        completed_count += 1
                        ticker = result["ticker"]

                        # Update cache with individual ticker data
                        self.data_cache["price_changes"][ticker] = result[
                            "price_change"
                        ]
                        self.data_cache["current_prices"][ticker] = result[
                            "current_price"
                        ]
                        self.data_cache["company_names"][ticker] = result[
                            "company_name"
                        ]

                        # Create basic ticker ranking entry
                        ticker_entry = {
                            "ticker": ticker,
                            "company_name": result["company_name"],
                            "current_price": result["current_price"],
                            "price_change": result["price_change"],
                            "sentiment": 0.0,  # Will be updated later
                            "rank": completed_count,
                            "articles": 0,  # Will be updated later
                        }

                        # Add to ticker rankings
                        if "ticker_rankings" not in self.data_cache:
                            self.data_cache["ticker_rankings"] = []

                        # Update or add ticker entry
                        existing_index = None
                        for j, existing in enumerate(
                            self.data_cache["ticker_rankings"]
                        ):
                            if existing["ticker"] == ticker:
                                existing_index = j
                                break

                        if existing_index is not None:
                            self.data_cache["ticker_rankings"][
                                existing_index
                            ] = ticker_entry
                        else:
                            self.data_cache["ticker_rankings"].append(ticker_entry)

                    # Schedule single UI update for the entire chunk
                    self.call_later(self.update_streaming_ticker_display)

                    # Update status with progress
                    progress = f"📊 Loaded {completed_count}/{len(tickers)} tickers..."
                    self.call_later(lambda msg=progress: self.update_status(msg))

                # Small delay between chunks to keep UI responsive
                time.sleep(ui_update_interval)

        # Start chunked streaming in background thread
        stream_thread = threading.Thread(target=chunked_stream_worker, daemon=True)
        stream_thread.start()

    def update_streaming_ticker_display(self) -> None:
        """Update ticker display with streaming data - throttled for responsiveness"""
        try:
            import time

            # Throttle updates to avoid overwhelming the UI
            current_time = time.time()
            if not hasattr(self, "_last_ticker_update"):
                self._last_ticker_update = 0

            # Only update every 200ms to keep UI responsive
            if current_time - self._last_ticker_update < 0.2:
                return

            self._last_ticker_update = current_time

            # Update tickers panel with current data
            tickers_panel = self.query_one("#tickers-panel", TickersPanel)
            ticker_rankings = self.data_cache.get("ticker_rankings", [])
            price_changes = self.data_cache.get("price_changes", {})
            current_prices = self.data_cache.get("current_prices", {})
            sector_rankings = self.data_cache.get("sector_rankings", [])

            tickers_panel.update_data(
                sector_rankings, ticker_rankings, price_changes, current_prices
            )

            # Also update interactive ticker table if on that tab
            try:
                ticker_table = self.query_one(InteractiveTickerTable)
                ticker_table.update_data(ticker_rankings, price_changes, current_prices)
            except Exception:
                pass  # Table might not be visible

        except Exception:
            pass  # Fail silently to avoid disrupting streaming

    def load_secondary_data_background(self) -> None:
        """Load secondary data in background"""
        try:
            # Run in background thread
            import threading

            thread = threading.Thread(
                target=self._fetch_secondary_data_thread, daemon=True
            )
            thread.start()

        except Exception as e:
            self.update_status(f"⚠️ Secondary loading error: {str(e)}")

    def _fetch_secondary_data_thread(self) -> None:
        """Background thread for fetching secondary data with chunked processing"""
        try:
            import time
            from ..core.financial_analyzer import fetch_all_data

            quick_mode = getattr(self, "quick_mode", False)

            # Phase 1: Fetch basic news and government data (lighter load)
            self.call_later(lambda: self.update_status("📰 Loading news data..."))

            # Fetch data in smaller chunks to avoid blocking
            (
                news_data,
                news_stats,
                government_data,
                policy_stats,
                market_data,
                market_historical_data,
            ) = fetch_all_data(quick_mode=quick_mode)

            # Update cache incrementally
            self.data_cache.update(
                {
                    "news_data": news_data,
                    "government_data": government_data,
                    "market_historical_data": market_historical_data,
                }
            )

            # Schedule UI updates on main thread
            self.call_later(self.update_news_panels)

            # Small delay to keep UI responsive
            time.sleep(0.1)

            # Phase 2: Start earnings data loading in chunks
            self.call_later(lambda: self.update_status("💰 Loading earnings data..."))
            self._load_earnings_data_chunked()

            # Phase 3: Mark secondary loading complete
            self.data_cache["loading_phase"] = "secondary_loaded"
            self.call_later(lambda: self.update_status("🧠 Completing analysis..."))

            # Start final analysis phase
            self.call_later(self.complete_analysis_background)

        except Exception as e:
            error_msg = str(e)
            self.call_later(
                lambda: self.update_status(f"⚠️ News data error: {error_msg}")
            )

    def _load_earnings_data_chunked(self):
        """Load earnings data in chunks to avoid UI blocking"""
        import threading
        import time
        from ..data.data_fetcher import MAJOR_TICKERS
        from ..core.earnings_fetcher import cached_get_ticker_quarterly_earnings

        def chunked_earnings_worker():
            """Worker for chunked earnings data loading"""
            try:
                quick_mode = getattr(self, "quick_mode", False)
                tickers = MAJOR_TICKERS[:15] if quick_mode else MAJOR_TICKERS[:30]

                chunk_size = 3  # Process 3 tickers' earnings at a time
                ui_update_interval = 0.2  # Update every 200ms
                completed_count = 0

                # Initialize earnings cache
                if "earnings_data" not in self.data_cache:
                    self.data_cache["earnings_data"] = {}

                # Process earnings in small chunks
                for i in range(0, len(tickers), chunk_size):
                    chunk = tickers[i : i + chunk_size]

                    # Process chunk
                    for ticker in chunk:
                        try:
                            earnings = cached_get_ticker_quarterly_earnings(ticker)
                            if earnings:
                                self.data_cache["earnings_data"][ticker] = earnings
                            completed_count += 1

                            # Update progress
                            progress = f"💰 Loaded earnings {completed_count}/{len(tickers)}..."
                            self.call_later(
                                lambda msg=progress: self.update_status(msg)
                            )

                        except Exception:
                            # Skip failed earnings data
                            completed_count += 1
                            continue

                    # Small delay between chunks to keep UI responsive
                    time.sleep(ui_update_interval)

                # Mark earnings loading complete
                self.call_later(lambda: self.update_status("✅ Earnings data loaded"))

            except Exception as e:
                error_msg = str(e)
                self.call_later(
                    lambda: self.update_status(f"⚠️ Earnings loading error: {error_msg}")
                )

        # Start earnings loading in background
        earnings_thread = threading.Thread(target=chunked_earnings_worker, daemon=True)
        earnings_thread.start()

    def complete_analysis_background(self) -> None:
        """Complete full analysis in background"""
        try:
            # Run in background thread
            import threading

            thread = threading.Thread(
                target=self._complete_analysis_thread, daemon=True
            )
            thread.start()

        except Exception as e:
            self.update_status(f"⚠️ Analysis error: {str(e)}")

    def _complete_analysis_thread(self) -> None:
        """Background thread for completing analysis with chunked processing"""
        try:
            # Run analysis in chunks to keep UI responsive
            self.call_later(self.update_dashboard_data_chunked)

        except Exception as e:
            error_msg = str(e)
            self.call_later(
                lambda: self.update_status(f"⚠️ Analysis error: {error_msg}")
            )

    async def update_dashboard_data_chunked(self) -> None:
        """Update dashboard data with chunked processing for responsiveness"""
        try:
            import asyncio

            # Skip full reload if we're in progressive loading mode
            if self.data_cache.get("loading_phase") in ["critical", "secondary"]:
                self.update_status("🔄 Completing analysis...")
            else:
                self.update_status("🔄 Refreshing data...")

            # Import here to avoid circular imports
            from ..core.financial_analyzer import analyze_all_data, fetch_all_data

            # Use cached data if available, otherwise fetch fresh
            if "news_data" in self.data_cache and "government_data" in self.data_cache:
                news_data = self.data_cache["news_data"]
                government_data = self.data_cache["government_data"]
                market_data = self.data_cache.get("market_data", {})
                market_historical_data = self.data_cache.get(
                    "market_historical_data", {}
                )
            else:
                # Fetch new data using the configured quick mode
                quick_mode = getattr(self, "quick_mode", False)
                (
                    news_data,
                    _,
                    government_data,
                    _,
                    market_data,
                    market_historical_data,
                ) = fetch_all_data(quick_mode=quick_mode)

            # Phase 1: Analyze core data (lighter processing)
            self.update_status("🧠 Analyzing sentiment...")
            await asyncio.sleep(0.05)  # Yield control to UI

            # Analyze data in chunks
            (
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
                _,
            ) = analyze_all_data(
                news_data, government_data, market_data, market_historical_data
            )

            # Phase 2: Update cache incrementally
            self.update_status("💾 Updating cache...")
            await asyncio.sleep(0.05)  # Yield control to UI

            # Store data for other tabs
            self.data_cache.update(
                {
                    "sentiment_analysis": sentiment_analysis,
                    "policy_analysis": policy_analysis,
                    "market_health": market_health,
                    "sector_rankings": sector_rankings,
                    "ticker_rankings": ticker_rankings,
                    "price_changes": price_changes,
                    "current_prices": current_prices,
                    "company_names": company_names,
                    "sentiment_scores": sentiment_scores,
                    "sentiment_details": sentiment_details,
                    "multi_ticker_articles": multi_ticker_articles,
                    "cross_ticker_analysis": cross_ticker_analysis,
                    "market_data": market_data,
                    "market_historical_data": market_historical_data,
                    "news_data": news_data,
                    "government_data": government_data,
                }
            )

            # Phase 3: Update UI panels in chunks
            await self._update_ui_panels_chunked(
                sentiment_analysis,
                policy_analysis,
                market_health,
                sector_rankings,
                ticker_rankings,
                price_changes,
                current_prices,
                multi_ticker_articles,
                cross_ticker_analysis,
                news_data,
                sentiment_scores,
                sentiment_details,
                market_data,
                market_historical_data,
            )

            # Update reactive variables
            self.current_sentiment = sentiment_analysis.get("average_sentiment", 0)
            self.last_update = datetime.now().strftime("%H:%M:%S")
            self.update_status(f"✅ Updated at {self.last_update}")

        except Exception as e:
            # Handle errors gracefully
            self.notify(f"Error updating data: {str(e)}", severity="error")
            self.update_status(f"❌ Error: {str(e)}")

    async def _update_ui_panels_chunked(
        self,
        sentiment_analysis,
        policy_analysis,
        market_health,
        sector_rankings,
        ticker_rankings,
        price_changes,
        current_prices,
        multi_ticker_articles,
        cross_ticker_analysis,
        news_data,
        sentiment_scores,
        sentiment_details,
        market_data,
        market_historical_data,
    ):
        """Update UI panels in chunks to maintain responsiveness"""
        import asyncio

        # Chunk 1: Overview tab panels (most critical)
        self.update_status("🎨 Updating overview...")
        try:
            summary_panel = self.query_one("#summary-panel", SummaryPanel)
            summary_panel.update_data(
                sentiment_analysis, policy_analysis, market_health, market_data
            )
        except Exception:
            pass
        await asyncio.sleep(0.05)  # Yield control to UI

        try:
            tickers_panel = self.query_one("#tickers-panel", TickersPanel)
            tickers_panel.update_data(
                sector_rankings, ticker_rankings, price_changes, current_prices
            )
        except Exception:
            pass
        await asyncio.sleep(0.05)

        # Chunk 2: Sector and multi-ticker panels
        self.update_status("📊 Updating sectors...")
        try:
            sectors_panel = self.query_one("#sectors-panel", SectorsPanel)
            sectors_panel.update_data(sector_rankings, price_changes)
        except Exception:
            pass
        await asyncio.sleep(0.05)

        try:
            multi_ticker_panel = self.query_one("#multi-ticker-panel", MultiTickerPanel)
            multi_ticker_panel.update_data(multi_ticker_articles, cross_ticker_analysis)
        except Exception:
            pass
        await asyncio.sleep(0.05)

        # Chunk 3: Interactive tickers tab
        self.update_status("🏆 Updating tickers...")
        try:
            ticker_table = self.query_one(InteractiveTickerTable)
            ticker_table.update_data(ticker_rankings, price_changes, current_prices)
        except Exception:
            pass
        await asyncio.sleep(0.05)

        # Chunk 4: News tab
        self.update_status("📰 Updating news...")
        try:
            news_tree = self.query_one("#news-tree", NewsTreeView)
            news_tree.update_news(news_data, sentiment_scores, sentiment_details)

            chart = self.query_one(RealTimeChart)
            if sentiment_analysis:
                chart.update_sentiment(sentiment_analysis.get("average_sentiment", 0))
        except Exception:
            pass
        await asyncio.sleep(0.05)

        # Chunk 5: Policy tab
        self.update_status("🏛️ Updating policy...")
        try:
            policy_tree = self.query_one("#policy-tree", PolicyTreeView)
            policy_tree.update_data(policy_analysis)
        except Exception:
            pass
        await asyncio.sleep(0.05)

        try:
            policy_summary_panel = self.query_one(
                "#policy-summary-panel", PolicySummaryPanel
            )
            policy_summary_panel.update_data(policy_analysis)
        except Exception:
            pass
        await asyncio.sleep(0.05)

        try:
            policy_timeline_panel = self.query_one(
                "#policy-timeline-panel", PolicyTimelinePanel
            )
            policy_timeline_panel.update_data(policy_analysis)
        except Exception:
            pass
        await asyncio.sleep(0.05)

        # Chunk 6: Market indices tab
        self.update_status("📈 Updating indices...")
        try:
            indices_panel = self.query_one("#market-indices-panel", MarketIndicesPanel)
            indices_panel.update_data(market_data, market_historical_data)
        except Exception:
            pass
        await asyncio.sleep(0.05)

    async def update_dashboard_data(self) -> None:
        """Update all dashboard data - now optimized for hot loading"""
        try:
            # Skip full reload if we're in progressive loading mode
            if self.data_cache.get("loading_phase") in ["critical", "secondary"]:
                self.update_status("🔄 Completing analysis...")
            else:
                self.update_status("🔄 Refreshing data...")

            # Import here to avoid circular imports
            from ..core.financial_analyzer import analyze_all_data, fetch_all_data

            # Use cached data if available, otherwise fetch fresh
            if "news_data" in self.data_cache and "government_data" in self.data_cache:
                news_data = self.data_cache["news_data"]
                government_data = self.data_cache["government_data"]
                market_data = self.data_cache.get("market_data", {})
                market_historical_data = self.data_cache.get(
                    "market_historical_data", {}
                )
            else:
                # Fetch new data using the configured quick mode
                quick_mode = getattr(self, "quick_mode", False)
                (
                    news_data,
                    _,
                    government_data,
                    _,
                    market_data,
                    market_historical_data,
                ) = fetch_all_data(quick_mode=quick_mode)

            # Analyze data
            (
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
                _,
            ) = analyze_all_data(
                news_data, government_data, market_data, market_historical_data
            )

            # Store data for other tabs
            self.data_cache = {
                "sentiment_analysis": sentiment_analysis,
                "policy_analysis": policy_analysis,
                "market_health": market_health,
                "sector_rankings": sector_rankings,
                "ticker_rankings": ticker_rankings,
                "price_changes": price_changes,
                "current_prices": current_prices,
                "company_names": company_names,
                "sentiment_scores": sentiment_scores,
                "sentiment_details": sentiment_details,
                "multi_ticker_articles": multi_ticker_articles,
                "cross_ticker_analysis": cross_ticker_analysis,
                "market_data": market_data,
                "market_historical_data": market_historical_data,
                "news_data": news_data,
                "government_data": government_data,
            }

            # Update Overview tab panels
            try:
                summary_panel = self.query_one("#summary-panel", SummaryPanel)
                summary_panel.update_data(
                    sentiment_analysis, policy_analysis, market_health, market_data
                )
            except Exception:
                pass

            try:
                tickers_panel = self.query_one("#tickers-panel", TickersPanel)
                tickers_panel.update_data(
                    sector_rankings, ticker_rankings, price_changes, current_prices
                )
            except Exception:
                pass

            try:
                sectors_panel = self.query_one("#sectors-panel", SectorsPanel)
                sectors_panel.update_data(sector_rankings, price_changes)
            except Exception:
                pass

            try:
                multi_ticker_panel = self.query_one(
                    "#multi-ticker-panel", MultiTickerPanel
                )
                multi_ticker_panel.update_data(
                    multi_ticker_articles, cross_ticker_analysis
                )
            except Exception:
                pass

            # Update Interactive Tickers tab
            try:
                ticker_table = self.query_one(InteractiveTickerTable)
                ticker_table.update_data(ticker_rankings, price_changes, current_prices)
            except Exception:
                pass

            # Update News Tree tab
            try:
                news_tree = self.query_one("#news-tree", NewsTreeView)
                news_tree.update_news(news_data, sentiment_scores, sentiment_details)

                chart = self.query_one(RealTimeChart)
                if sentiment_analysis:
                    chart.update_sentiment(
                        sentiment_analysis.get("average_sentiment", 0)
                    )
            except Exception:
                pass

            # Update Policy tab
            try:
                policy_tree = self.query_one("#policy-tree", PolicyTreeView)
                policy_tree.update_data(policy_analysis)
            except Exception:
                pass

            try:
                policy_summary_panel = self.query_one(
                    "#policy-summary-panel", PolicySummaryPanel
                )
                policy_summary_panel.update_data(policy_analysis)
            except Exception:
                pass

            try:
                policy_timeline_panel = self.query_one(
                    "#policy-timeline-panel", PolicyTimelinePanel
                )
                policy_timeline_panel.update_data(policy_analysis)
            except Exception:
                pass

            # Update Market Indices tab panel
            try:
                indices_panel = self.query_one(
                    "#market-indices-panel", MarketIndicesPanel
                )
                indices_panel.update_data(market_data, market_historical_data)
            except Exception:
                pass

            # Update reactive variables
            self.current_sentiment = sentiment_analysis.get("average_sentiment", 0)
            self.last_update = datetime.now().strftime("%H:%M:%S")

            self.update_status(f"✅ Updated at {self.last_update}")

        except Exception as e:
            # Handle errors gracefully
            self.notify(f"Error updating data: {str(e)}", severity="error")
            self.update_status(f"❌ Error: {str(e)}")

    def update_basic_panels(self) -> None:
        """Update basic panels with price data during progressive loading"""
        try:
            price_changes = self.data_cache.get("price_changes", {})
            current_prices = self.data_cache.get("current_prices", {})
            company_names = self.data_cache.get("company_names", {})
            market_data = self.data_cache.get("market_data", {})

            # Use existing ticker rankings if available, otherwise create basic ones
            ticker_rankings = self.data_cache.get("ticker_rankings", [])

            # If no ticker rankings yet and we have price data, create basic ones
            if not ticker_rankings and price_changes:
                ticker_rankings = []
                for i, ticker in enumerate(list(price_changes.keys())[:20]):
                    ticker_rankings.append(
                        {
                            "ticker": ticker,
                            "company_name": company_names.get(ticker, ticker),
                            "current_price": current_prices.get(ticker, 0.0),
                            "price_change": price_changes.get(ticker, 0.0),
                            "sentiment": 0.0,  # Will be updated later
                            "rank": i + 1,
                            "articles": 0,  # Will be updated later
                        }
                    )
                self.data_cache["ticker_rankings"] = ticker_rankings

            # Update tickers panel with available data
            try:
                tickers_panel = self.query_one("#tickers-panel", TickersPanel)
                sector_rankings = self.data_cache.get("sector_rankings", [])
                tickers_panel.update_data(
                    sector_rankings, ticker_rankings, price_changes, current_prices
                )
            except Exception:
                pass

            # Update summary panel with basic market data
            try:
                summary_panel = self.query_one("#summary-panel", SummaryPanel)
                basic_sentiment = {
                    "market_mood": "Loading...",
                    "average_sentiment": 0.0,
                }
                summary_panel.update_data(basic_sentiment, {}, {}, market_data)
            except Exception:
                pass

        except Exception as e:
            self.notify(f"Error updating basic panels: {str(e)}", severity="warning")

    def update_news_panels(self) -> None:
        """Update news-related panels during progressive loading"""
        try:
            news_data = self.data_cache.get("news_data", [])

            # Update news tree with available data
            try:
                news_tree = self.query_one("#news-tree", NewsTreeView)
                # Use empty sentiment data for now - will be updated in complete analysis
                news_tree.update_news(news_data, {}, [])
            except Exception:
                pass

            # Update policy tree if government data is available
            government_data = self.data_cache.get("government_data", [])
            if government_data:
                try:
                    policy_tree = self.query_one("#policy-tree", PolicyTreeView)
                    # Create basic policy analysis structure
                    basic_policy_analysis = {
                        "articles": government_data,
                        "categories": {},
                        "sentiment_summary": {"average_sentiment": 0.0},
                    }
                    policy_tree.update_data(basic_policy_analysis)
                except Exception:
                    pass

        except Exception as e:
            self.notify(f"Error updating news panels: {str(e)}", severity="warning")

    def on_background_data_update(self, data_type: str, identifier: str) -> None:
        """Handle background data updates for hot loading with throttling"""
        try:
            import time

            # Throttle background updates to avoid overwhelming the UI
            current_time = time.time()
            if not hasattr(self, "_last_bg_update"):
                self._last_bg_update = {}

            # Only update each data type every 500ms
            if data_type in self._last_bg_update:
                if current_time - self._last_bg_update[data_type] < 0.5:
                    return

            self._last_bg_update[data_type] = current_time

            if data_type == "prices":
                # Update price-related panels when new price data arrives
                self.call_later(self.refresh_price_panels_throttled)
            elif data_type == "news":
                # Update news-related panels when new news arrives
                self.call_later(self.refresh_news_panels_throttled)
            elif data_type == "market":
                # Update market data panels
                self.call_later(self.refresh_market_panels_throttled)

        except Exception:
            # Handle errors silently to avoid disrupting background updates
            pass

    def refresh_price_panels_throttled(self) -> None:
        """Refresh panels that depend on price data with throttling"""
        try:
            import time

            # Throttle price panel updates
            current_time = time.time()
            if not hasattr(self, "_last_price_refresh"):
                self._last_price_refresh = 0

            if current_time - self._last_price_refresh < 1.0:  # Max once per second
                return

            self._last_price_refresh = current_time

            # Get fresh price data from cache
            from ..data.cached_data_fetcher import (
                get_multiple_ticker_current_prices,
                get_multiple_ticker_prices,
            )
            from ..data.data_fetcher import MAJOR_TICKERS

            quick_mode = getattr(self, "quick_mode", False)
            tickers = MAJOR_TICKERS[:20] if quick_mode else MAJOR_TICKERS[:50]

            price_changes = get_multiple_ticker_prices(tickers)
            current_prices = get_multiple_ticker_current_prices(tickers)

            # Update cache
            self.data_cache.update(
                {
                    "price_changes": price_changes,
                    "current_prices": current_prices,
                }
            )

            # Update tickers panel if it exists
            try:
                tickers_panel = self.query_one("#tickers-panel", TickersPanel)
                ticker_rankings = self.data_cache.get("ticker_rankings", [])
                sector_rankings = self.data_cache.get("sector_rankings", [])
                tickers_panel.update_data(
                    sector_rankings, ticker_rankings, price_changes, current_prices
                )
            except Exception:
                pass

        except Exception:
            pass

    def refresh_news_panels_throttled(self) -> None:
        """Refresh panels that depend on news data with throttling"""
        try:
            import time

            # Throttle news panel updates
            current_time = time.time()
            if not hasattr(self, "_last_news_refresh"):
                self._last_news_refresh = 0

            if current_time - self._last_news_refresh < 2.0:  # Max once per 2 seconds
                return

            self._last_news_refresh = current_time

            # Update news tree if it exists
            try:
                news_tree = self.query_one("#news-tree", NewsTreeView)
                news_data = self.data_cache.get("news_data", [])
                sentiment_scores = self.data_cache.get("sentiment_scores", {})
                sentiment_details = self.data_cache.get("sentiment_details", [])
                news_tree.update_news(news_data, sentiment_scores, sentiment_details)
            except Exception:
                pass

        except Exception:
            pass

    def refresh_market_panels_throttled(self) -> None:
        """Refresh panels that depend on market data with throttling"""
        try:
            import time

            # Throttle market panel updates
            current_time = time.time()
            if not hasattr(self, "_last_market_refresh"):
                self._last_market_refresh = 0

            if (
                current_time - self._last_market_refresh < 1.5
            ):  # Max once per 1.5 seconds
                return

            self._last_market_refresh = current_time

            # Get fresh market data
            from ..data.cached_data_fetcher import cached_get_market_data_optimized

            market_data = cached_get_market_data_optimized()
            self.data_cache["market_data"] = market_data

            # Update summary panel if it exists
            try:
                summary_panel = self.query_one("#summary-panel", SummaryPanel)
                sentiment_analysis = self.data_cache.get("sentiment_analysis", {})
                policy_analysis = self.data_cache.get("policy_analysis", {})
                market_health = self.data_cache.get("market_health", {})
                summary_panel.update_data(
                    sentiment_analysis, policy_analysis, market_health, market_data
                )
            except Exception:
                pass

        except Exception:
            pass

    def on_unmount(self) -> None:
        """Cleanup when dashboard is closed"""
        try:
            if self.background_fetcher:
                self.background_fetcher.stop_background_fetching()
        except Exception:
            pass

    def update_status(self, message: str) -> None:
        """Update status bar"""
        try:
            status_bar = self.query_one("#status-bar", Static)
            refresh_status = "ON" if self.auto_refresh_enabled else "OFF"
            status_bar.update(f"🔄 Auto-refresh: {refresh_status} | {message}")
        except Exception:
            pass

    def action_refresh(self) -> None:
        """Manual refresh action"""
        self.call_later(self.update_dashboard_data)

    def action_toggle_filter(self) -> None:
        """Toggle filter visibility"""
        try:
            filters = self.query_one(".controls-panel")
            filters.display = not filters.display
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to specific tab (overview, tickers, news, policy)"""
        try:
            tabbed_content = self.query_one(TabbedContent)
            tabbed_content.active = tab_id
        except Exception:
            pass

    def action_export_data(self) -> None:
        """Export current data"""
        self.notify(
            "Export functionality would be implemented here", severity="information"
        )

    def action_open_article_url(self) -> None:
        """Open the currently selected article URL in browser"""
        if self.current_article_url:
            import webbrowser

            try:
                webbrowser.open(self.current_article_url)
                self.notify("Opening article in browser...", severity="information")
            except Exception as e:
                self.notify(f"Error opening URL: {str(e)}", severity="error")
        else:
            self.notify(
                "No article selected. Click on an article in the News tab first.",
                severity="warning",
            )


def run_textual_dashboard():
    """Run the Stockholm dashboard"""
    app = StockholmDashboard()
    app.run()


def run_enhanced_textual_dashboard(quick_mode=False, verbose=False):
    """Run the Stockholm dashboard with configuration options"""
    app = StockholmDashboard()

    # Store configuration in the app for use by data fetching
    app.quick_mode = quick_mode
    app.verbose_mode = verbose

    if verbose:
        # Show a brief startup message before launching the dashboard
        print("🚀 Launching Stockholm Dashboard...")
        print("⚡ Quick mode:", "ON" if quick_mode else "OFF")
        print("📊 Loading interface...\n")

    app.run()


if __name__ == "__main__":
    run_textual_dashboard()
