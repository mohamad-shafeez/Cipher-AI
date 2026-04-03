import yfinance as yf
import re

class MarketAnalystSkill:
    def __init__(self):
        print(">> Market Analyst Skill: ONLINE (Yahoo Finance Active)")

    def _extract_ticker(self, cmd):
        """Attempts to find a ticker symbol in the command."""
        # Look for words that are all uppercase or specifically marked
        # Example: "analyze stock NVDA"
        match = re.search(r"stock ([\w.]+)", cmd)
        if match:
            return match.group(1).upper()
        
        # Fallback: take the last word if it's a short string
        words = cmd.split()
        if words:
            potential = words[-1].upper()
            if len(potential) <= 5: # Most tickers are 1-5 chars
                return potential
        return None

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- TRIGGER DETECTION ---
            if not any(w in cmd for w in ["stock", "market", "trading price", "analyze"]):
                return None

            ticker_symbol = self._extract_ticker(cmd)
            
            if not ticker_symbol:
                return "Sir, please specify the ticker symbol of the company you wish to analyze."

            print(f">> [MarketAnalyst] Analyzing data for: {ticker_symbol}...")
            
            ticker = yf.Ticker(ticker_symbol)
            
            # Use basic info to check if ticker is valid
            info = ticker.info
            if 'regularMarketPrice' not in info and 'currentPrice' not in info:
                return f"Sir, I could not find a valid market entry for {ticker_symbol}."

            # Fetch 1 year history for trend analysis
            hist = ticker.history(period="1y")
            
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
            high_52 = info.get("fiftyTwoWeekHigh", "N/A")
            low_52 = info.get("fiftyTwoWeekLow", "N/A")
            currency = info.get("currency", "USD")

            # Simple trend calculation
            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
            percent_change = ((end_price - start_price) / start_price) * 100
            trend = "bullish" if percent_change > 0 else "bearish"

            # Formulate the 3-sentence professional response
            analysis = (
                f"Sir, {ticker_symbol} is currently trading at {current_price} {currency}. "
                f"The stock has shown a {trend} trend over the last year with a {percent_change:.1f} percent change, "
                f"ranging from a low of {low_52} to a high of {high_52}. "
                f"Market activity remains consistent with a recorded volume of {info.get('volume', 'N/A')} units."
            )

            return analysis

        except Exception as e:
            print(f"[MarketAnalyst Error] {e}")
            return None