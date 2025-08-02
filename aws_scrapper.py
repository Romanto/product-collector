import os
import asyncio
from playwright.async_api import async_playwright, Page
import random
import json
from typing import Dict
from playwright_stealth import Stealth
from dotenv import load_dotenv

# BrightData proxy configuration
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

async def get_resolution() -> dict:
    """Returns a realistic screen resolution based on common modern screen sizes."""
    resolutions = [
        {"width": 1920, "height": 1080}, # Full HD
        {"width": 1366, "height": 768},  # Common laptop
        {"width": 1440, "height": 900},  # Mid-range
        {"width": 2560, "height": 1440}, # 2K
        {"width": 1600, "height": 900}   # Common desktop
    ]
    weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # Probability distribution
    return random.choices(resolutions, weights=weights, k=1)[0]

def get_languages():
    """Return a random language from a predefined tuple."""
    custom_languages = [
    ("en-US", "en-GB", "en"),  # English: US, UK, Generic
    ("fr-FR", "fr-CA", "fr"),  # French: France, Canada, Generic
    ("de-DE", "de-AT", "de"),  # German: Germany, Austria, Generic
    ("es-ES", "es-MX", "es"),  # Spanish: Spain, Mexico, Generic
    ("it-IT", "it"),           # Italian: Italy, Generic
    ("pt-PT", "pt-BR", "pt"),  # Portuguese: Portugal, Brazil, Generic
    ("nl-NL", "nl"),           # Dutch: Netherlands, Generic
    ("ja-JP", "ja"),           # Japanese: Japan, Generic
    ("zh-CN", "zh-TW", "zh"),  # Chinese: Simplified (Mainland), Traditional (Taiwan), Generic
    ("ru-RU", "ru"),           # Russian: Russia, Generic
    ]
    return random.choice(custom_languages)

async def get_scroll(page: Page, max_scrolls: int = random.randint(1, 6)) -> None:
    try:
        """Simulates human-like page scrolling with natural pauses and variations."""
        viewport_height = await page.evaluate("window.innerHeight")
        document_height = await page.evaluate("document.body.scrollHeight")
        current_position = await page.evaluate("window.scrollY")
        
        for _ in range(random.randint(1, max_scrolls)):
            # Calculate random scroll distance (30-70% of viewport)
            scroll_distance = random.randint(int(viewport_height * 0.3), int(viewport_height * 0.7))
            
            # Decide scroll direction (down 80% chance, up 20% chance if not at top)
            if current_position > 0 and random.random() < 0.2:
                scroll_distance = -scroll_distance
                
            # Don't scroll beyond document boundaries
            target_position = max(0, min(current_position + scroll_distance, document_height - viewport_height))
            
            # Perform smooth scroll with human-like timing
            await page.evaluate(f"""
                window.scrollTo({{ 
                    top: {target_position},
                    behavior: 'smooth'
                }})
            """)
            
            # Random pause to mimic reading
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            current_position = target_position
            if current_position >= document_height - viewport_height:
                break
    except Exception as e:
        print(f"Exception accured during get_scroll: {e}")

async def get_mouse(page: Page, max_moves: int = random.randint(2, 6)) -> None:
    """Simulates human-like mouse movements with natural curves."""
    viewport_size = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
    mouse = page.mouse
    
    for _ in range(random.randint(2, max_moves)):
        # Generate random target point within viewport
        x = random.randint(50, viewport_size['width'] - 50)
        y = random.randint(50, viewport_size['height'] - 50)
        
        # Current mouse position (approximated)
        current_x = random.randint(0, viewport_size['width'])
        current_y = random.randint(0, viewport_size['height'])
        
        # Create bezier curve points for natural movement
        control_x1 = current_x + (x - current_x) * random.uniform(0.3, 0.7)
        control_y1 = current_y + (y - current_y) * random.uniform(0.3, 0.7)
        
        # Move mouse with human-like speed
        steps = random.randint(10, 20)
        for i in range(steps):
            t = i / steps
            # Quadratic bezier curve calculation
            bx = (1-t)**2 * current_x + 2*(1-t)*t * control_x1 + t**2 * x
            by = (1-t)**2 * current_y + 2*(1-t)*t * control_y1 + t**2 * y
            await mouse.move(bx, by)
            await asyncio.sleep(random.uniform(0.01, 0.03))
        
        # Random pause between movements
        await asyncio.sleep(random.uniform(0.2, 0.8))

async def press_keys(page, delay: float = 0.2):
    """
    Simulates pressing a list of keys one by one with optional delay.

    Args:
        page: Playwright page object
        keys: List of key names (e.g., ["ArrowDown", "Enter", "a", "Control+A"])
        delay: Delay in seconds between key presses
    """
    keyboard_keys = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End", "PageUp", "PageDown", "Tab", "Enter"]
    keys = random.choices(keyboard_keys, k=random.randint(1, len(keyboard_keys) - 1))
    for key in keys:
        await page.keyboard.press(key)
        await page.wait_for_timeout(delay * random.randint(600, 1200))

async def click_continue_shopping_if_present(page):
    """
    Clicks the 'Continue shopping' button if it appears on the page.
    Matches based on text, class, and alt attribute.
    """
    try:
        # Primary selector: exact visible text
        await get_mouse(page=page)
        await page.wait_for_timeout(random.randint(1, 3) * random.randint(1600, 5200))
        button = page.locator('button:has-text("Continue shopping")')
        if await button.is_visible():
            await button.click()
            print("✅ Clicked 'Continue shopping' via text match")
            await press_keys(page=page)
            return

        # Secondary selector: matching class and alt attribute
        alt_button = page.locator('button.a-button-text[alt="Continue shopping"]')
        if await alt_button.is_visible():
            await alt_button.click()
            print("✅ Clicked 'Continue shopping' via class+alt match")
            return

        print("⚠️ 'Continue shopping' button not found")
    except Exception as e:
        print(f"❌ Error clicking 'Continue shopping': {e}")


async def get_user_agent(browser_type: str) -> Dict[str, str]:
    """Returns a browser-compatible user agent based on the browser type."""
    user_agents = {
        'chromium': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ],
        'firefox': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
    }
    
    return random.choice(user_agents.get(browser_type.lower(), user_agents['chromium']))

async def main(url):
    try:
        async with async_playwright() as p:
            browser_type = random.choice(['chromium', 'firefox'])
            browser_launcher = getattr(p, browser_type)
            browser = await browser_launcher.launch(headless=False, args=["--enable-logging=stderr", "--v=1"])
            context = await browser.new_context(user_agent=await get_user_agent(browser_type=browser_type),
                                                java_script_enabled=True,
                                                viewport=await get_resolution(),
                                                proxy={"server": proxy_server,
                                                       "username": proxy_username,
                                                       "password": proxy_password
                                                }
                                            )
            stealth = Stealth(
            navigator_languages_override=get_languages(),
            init_scripts_only=True
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            await click_continue_shopping_if_present(page)
            # Check for CAPTCHA
            captcha = await page.query_selector('input#captchacharacters')
            if captcha:
                print(f"❌ CAPTCHA detected for {url}")
                await browser.close()
            selected_strategies = random.choices([get_scroll, get_mouse, press_keys], k=2)
            await selected_strategies[random.randint(0, 1)](page=page)
            await selected_strategies[random.randint(0, 1)](page=page)
            await selected_strategies[random.randint(0, 1)](page=page)
            url = page.url
            html = await page.content()
            await browser.close()
            return html, url
    except Exception as e:
        print(f"❌ Something went wrong {e}")
        await browser.close()
