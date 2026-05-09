import requests
from bs4 import BeautifulSoup
import re
import os

class WebScoutSkill:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        print(">> Web Scout Skill: ONLINE (Scraper Active)")

    def _search_amazon(self, product_name):
        """Searches Amazon and extracts the first valid price found."""
        search_url = f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}"
        
        try:
            print(f">> [WebScout] Accessing Amazon archives for: {product_name}...")
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 503:
                return "Sir, Amazon has detected my probe and blocked the request. Please try again later."
                
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Logic to find price whole and fraction
            prices = []
            price_blocks = soup.find_all('span', class_='a-price')
            
            for block in price_blocks:
                whole = block.find('span', class_='a-price-whole')
                fraction = block.find('span', class_='a-price-fraction')
                if whole:
                    price_str = whole.text.replace(',', '').replace('.', '').strip()
                    if fraction:
                        price_str += "." + fraction.text.strip()
                    try:
                        prices.append(float(price_str))
                    except:
                        continue
            
            if prices:
                # We usually want the lowest price from the first page results
                lowest = min(prices)
                return f"Sir, I have scouted the market. The lowest price for {product_name} on Amazon is approximately ${lowest:.2f}."
            else:
                return f"Sir, I found the listings for {product_name}, but the pricing data is currently obscured or unavailable."

        except Exception as e:
            print(f"[WebScout Error] {e}")
            return "Sir, I encountered a network error while scouting the product."

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- TRIGGER DETECTION ---
            # Commands like: "scout the price of [item] on amazon" or "price of [item] on amazon"
            if "price of" not in cmd or "on amazon" not in cmd:
                return None

            # --- EXTRACTION ---
            # Extract everything between 'price of' and 'on amazon'
            match = re.search(r"price of (.*?) on amazon", cmd)
            if not match:
                return None

            product_target = match.group(1).strip()
            
            if not product_target:
                return "Sir, please specify which product you would like me to scout."

            return self._search_amazon(product_target)

        except Exception as e:
            print(f"[WebScout Error] {e}")
            return None