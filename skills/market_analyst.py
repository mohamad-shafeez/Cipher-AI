import re
from typing import Optional

class MarketAnalystSkill:
    """
    Cipher Skill — Market Analyst (Stealth Boot Version)
    Advanced financial data retrieval using Yahoo Finance.
    """
    def __init__(self):
        print(">> Market Analyst Skill: ONLINE (Advanced Quantitative Engine Active)")

    def _extract_ticker(self, cmd: str) -> Optional[str]:
        match = re.search(r"(?:stock|ticker|analyze|price of)\s+([a-zA-Z.-]{1,5})", cmd)
        if match:
            return match.group(1).upper()
        
        words = cmd.split()
        if words:
            potential = words[-1].upper()
            if 1 <= len(potential) <= 5 and potential.isalpha(): 
                return potential
        return None

    def _format_large_number(self, num) -> str:
        if not num or num == "N/A": return "N/A"
        try:
            num = float(num)
            if num >= 1_000_000_000_000:
                return f"{num / 1_000_000_000_000:.2f}T"
            elif num >= 1_000_000_000:
                return f"{num / 1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"{num / 1_000_000:.2f}M"
            return str(num)
        except ValueError:
            return str(num)

    def execute(self, command: str) -> Optional[str]:
        if not command:
            return None
        cmd = command.lower().strip()

        if not any(w in cmd for w in ["stock", "market", "trading price", "analyze", "ticker"]):
            return None

        ticker_symbol = self._extract_ticker(cmd)
        if not ticker_symbol:
            return "Sir, please specify the exact ticker symbol of the company."

        print(f">> [MarketAnalyst] Fetching advanced telemetry for: {ticker_symbol}...")
        
        # ── THE STEALTH FIX: Lazy Import bypasses the boot crash ──
        try:
            import yfinance as yf
        except ImportError:
            return "Sir, yfinance is not installed properly. Unable to fetch market data."

        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            if not current_price:
                return f"Sir, I could not find a valid market entry for ticker symbol '{ticker_symbol}'."

            currency = info.get("currency", "USD")
            high_52 = info.get("fiftyTwoWeekHigh", "N/A")
            low_52 = info.get("fiftyTwoWeekLow", "N/A")
            volume = self._format_large_number(info.get("volume"))
            market_cap = self._format_large_number(info.get("marketCap"))
            
            pe_ratio = info.get("trailingPE", "N/A")
            ma_50 = info.get("fiftyDayAverage", "N/A")
            ma_200 = info.get("twoHundredDayAverage", "N/A")

            hist = ticker.history(period="1y")
            if not hist.empty:
                start_price = hist["Close"].iloc[0]
                end_price = hist["Close"].iloc[-1]
                percent_change = ((end_price - start_price) / start_price) * 100
                trend = "bullish 📈" if percent_change > 0 else "bearish 📉"
            else:
                percent_change = 0
                trend = "neutral ➖"

            report = (
                f"**Market Telemetry: {ticker_symbol.upper()}**\n\n"
                f"Sir, {ticker_symbol.upper()} is currently trading at **{current_price} {currency}**.\n\n"
                f"**📊 Trend Analysis (1-Year)**\n"
                f"The stock is currently **{trend}**, showing a {percent_change:.2f}% shift. "
                f"It has ranged from a 52-week low of {low_52} to a high of {high_52}.\n\n"
                f"**⚙️ Core Fundamentals**\n"
                f"• **Market Cap:** {market_cap}\n"
                f"• **P/E Ratio:** {pe_ratio if isinstance(pe_ratio, str) else f'{pe_ratio:.2f}'}\n"
                f"• **24h Volume:** {volume}\n\n"
                f"**📈 Technical Indicators**\n"
                f"• **50-Day Moving Avg:** {ma_50 if isinstance(ma_50, str) else f'{ma_50:.2f}'}\n"
                f"• **200-Day Moving Avg:** {ma_200 if isinstance(ma_200, str) else f'{ma_200:.2f}'}\n"
            )
            return report

        except Exception as e:
            print(f"[MarketAnalyst Error] {e}")
            return f"Sir, I encountered a network error while fetching data for {ticker_symbol}."