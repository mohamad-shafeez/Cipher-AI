"""
Cipher Skill — Image Forge
Organ: The Artist
AI image generation via Bing Image Creator (free, no paid API key).
Uses your Microsoft account cookie — no subscription required.
16GB RAM build: supports batch generation and higher quality prompts.
"""

import os
import re
import time
import urllib.request
from datetime import datetime


OUTPUT_DIR = "generated_code"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")


class ImageForgeSkill:
    def __init__(self):
        os.makedirs(IMAGES_DIR, exist_ok=True)
        print(">> Image Forge: ONLINE")

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        triggers = [
            "generate image",
            "create image",
            "make image",
            "draw image",
            "generate picture",
            "create picture",
            "make picture",
            "image of",
            "picture of",
            "draw me",
            "render image",
            "ai image",
        ]

        matched = next((t for t in triggers if t in cmd), None)
        if not matched:
            return None

        # Extract prompt — everything after the trigger
        prompt = command
        for t in triggers:
            prompt = re.sub(re.escape(t), "", prompt, flags=re.IGNORECASE).strip()

        prompt = re.sub(r'^(of|a|an|the|me)\s+', '', prompt, flags=re.IGNORECASE).strip()

        if not prompt:
            return "What image should I generate? Usage: generate image [description]"

        return self._generate_image(prompt)

    def _generate_image(self, prompt: str) -> str:
        """
        Generate image via Bing Image Creator using the bing-image-creator library
        or a direct HTTP approach with your Microsoft _U cookie.
        """

        # ── METHOD 1: BingImageCreator library ────────────────────────────
        try:
            from BingImageCreator import ImageGen

            cookie = self._load_cookie()
            if not cookie:
                return (
                    "Bing Image Forge needs your Microsoft _U cookie.\n"
                    "1. Log into bing.com/images/create in your browser\n"
                    "2. Open DevTools (F12) → Application → Cookies → bing.com\n"
                    "3. Copy the value of the '_U' cookie\n"
                    "4. Add it to your .env file: BING_COOKIE=your_cookie_here"
                )

            gen = ImageGen(auth_cookie=cookie)
            image_links = gen.get_images(prompt)

            if not image_links:
                return f"Bing returned no images for: '{prompt}'. Try a different description."

            # Download and save images
            saved = self._download_images(image_links, prompt)
            if saved:
                return f"Generated {len(saved)} image(s) for '{prompt}':\n" + "\n".join(saved)
            else:
                return f"Images generated but download failed. URLs: {image_links[0]}"

        except ImportError:
            pass  # Fall through to method 2

        # ── METHOD 2: httpx direct approach (no extra library) ────────────
        try:
            return self._bing_direct(prompt)
        except Exception as e:
            return (
                f"Image Forge needs BingImageCreator library.\n"
                f"Install: pip install BingImageCreator\n"
                f"Error: {e}"
            )

    def _bing_direct(self, prompt: str) -> str:
        """
        Direct Bing Image Creator request using requests + your _U cookie.
        Fallback if BingImageCreator library isn't installed.
        """
        import requests

        cookie = self._load_cookie()
        if not cookie:
            return (
                "Bing Image Forge needs your Microsoft _U cookie.\n"
                "Add BING_COOKIE=your_value to your .env file.\n"
                "Get it from: bing.com/images/create → F12 → Cookies → _U"
            )

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Cookie": f"_U={cookie}",
            "Referer": "https://www.bing.com/images/create",
        })

        # Submit generation request
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://www.bing.com/images/create?q={encoded_prompt}&rt=4&FORM=GENCRE"

        response = session.post(url, allow_redirects=True, timeout=30)

        # Extract image URLs from response
        image_urls = re.findall(
            r'src="(https://th\.bing\.com/th/id/[^"]+)"',
            response.text
        )

        # Clean duplicates and filter thumbnails
        seen = set()
        clean_urls = []
        for u in image_urls:
            base = u.split("?")[0]
            if base not in seen and "pid=ImgGn" not in u:
                seen.add(base)
                clean_urls.append(u)

        if not clean_urls:
            return f"No images returned by Bing for: '{prompt}'. Check your cookie or try a simpler prompt."

        saved = self._download_images(clean_urls[:4], prompt)
        if saved:
            return f"Generated {len(saved)} image(s) for '{prompt}':\n" + "\n".join(saved)
        else:
            return f"Images generated. First URL: {clean_urls[0]}"

    def _download_images(self, urls: list, prompt: str) -> list[str]:
        """Download image URLs and save to disk."""
        saved = []
        safe_prompt = re.sub(r'[^\w\s-]', '', prompt).strip().replace(' ', '_')[:30]
        timestamp = datetime.now().strftime('%H%M%S')

        for i, url in enumerate(urls[:4]):
            try:
                filename = f"{safe_prompt}_{timestamp}_{i+1}.jpg"
                filepath = os.path.join(IMAGES_DIR, filename)

                import requests
                img_response = requests.get(url, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                })

                if img_response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(img_response.content)
                    saved.append(filepath)
                    time.sleep(0.3)  # Polite delay between downloads

            except Exception:
                continue

        return saved

    def _load_cookie(self) -> str | None:
        """
        Load Bing _U cookie from:
        1. .env file (BING_COOKIE=...)
        2. Environment variable
        """
        # Try .env file first
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        import os
        cookie = os.environ.get("BING_COOKIE", "").strip()
        if cookie:
            return cookie

        # Try reading .env manually as fallback
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("BING_COOKIE="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except FileNotFoundError:
            pass

        return None

    def list_generated(self) -> str:
        """List all previously generated images."""
        try:
            files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(('.jpg', '.png', '.webp'))]
            if not files:
                return "No images generated yet."
            files.sort(reverse=True)
            recent = files[:10]
            return f"Generated images ({len(files)} total):\n" + "\n".join(
                f"  {f}" for f in recent
            )
        except Exception as e:
            return f"Could not list images: {e}"