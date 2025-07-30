import argparse
import asyncio
import json
import os
import random
import re
import sys
from abc import ABC, abstractmethod

# from functools import partial  # Unused import removed
from typing import Any
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import aiofiles
import markdown
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from html_to_markdown import convert_to_markdown
from pydoll.browser.chromium import Chrome  # type: ignore
from pydoll.browser.options import ChromiumOptions  # type: ignore

# Note: Resource blocking feature temporarily disabled - imports not available in current Pydoll version
from tqdm.asyncio import tqdm

# Load environment variables
load_dotenv()

# Configuration from environment variables
SUBSTACK_EMAIL = os.getenv("SUBSTACK_EMAIL", "")
SUBSTACK_PASSWORD = os.getenv("SUBSTACK_PASSWORD", "")
USE_PREMIUM = os.getenv("USE_PREMIUM", "false").lower() == "true"
BASE_SUBSTACK_URL = os.getenv("DEFAULT_SUBSTACK_URL", "https://www.thefitzwilliam.com/")
NUM_POSTS_TO_SCRAPE = int(os.getenv("NUM_POSTS_TO_SCRAPE", "0"))
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"  # Default to non-headless for user intervention
BROWSER_PATH = os.getenv("BROWSER_PATH", "")
USER_AGENT = os.getenv("USER_AGENT", "")

# Directory configuration
BASE_MD_DIR = "substack_md_files"
BASE_HTML_DIR = "substack_html_pages"
HTML_TEMPLATE = "author_template.html"
JSON_DATA_DIR = "data"


def extract_main_part(url: str) -> str:
    """Extract the main part of a domain from a URL."""
    parts = urlparse(url).netloc.split(".")
    return parts[1] if parts[0] == "www" else parts[0]


async def generate_html_file(author_name: str) -> None:
    """Generates a HTML file for the given author."""
    if not os.path.exists(BASE_HTML_DIR):
        os.makedirs(BASE_HTML_DIR)

    json_path = os.path.join(JSON_DATA_DIR, f"{author_name}.json")
    async with aiofiles.open(json_path, encoding="utf-8") as file:
        content = await file.read()
        essays_data = json.loads(content)

    embedded_json_data = json.dumps(essays_data, ensure_ascii=False, indent=4)

    async with aiofiles.open(HTML_TEMPLATE, encoding="utf-8") as file:
        html_template = await file.read()

    html_with_data = html_template.replace("<!-- AUTHOR_NAME -->", author_name).replace(
        '<script type="application/json" id="essaysData"></script>',
        f'<script type="application/json" id="essaysData">{embedded_json_data}</script>',
    )
    html_with_author = html_with_data.replace("author_name", author_name)

    html_output_path = os.path.join(BASE_HTML_DIR, f"{author_name}.html")
    async with aiofiles.open(html_output_path, "w", encoding="utf-8") as file:
        await file.write(html_with_author)


class BaseSubstackScraper(ABC):
    """Abstract base class for Substack scrapers."""

    def __init__(
        self, base_substack_url: str, md_save_dir: str, html_save_dir: str, delay_range: tuple[int, int] = (1, 3)
    ):
        if not base_substack_url.endswith("/"):
            base_substack_url += "/"
        self.base_substack_url = base_substack_url
        self.writer_name = extract_main_part(base_substack_url)

        md_save_dir = f"{md_save_dir}/{self.writer_name}"
        self.md_save_dir = md_save_dir
        self.html_save_dir = f"{html_save_dir}/{self.writer_name}"

        # Create directories if they don't exist
        os.makedirs(md_save_dir, exist_ok=True)
        print(f"Created md directory {md_save_dir}")
        os.makedirs(self.html_save_dir, exist_ok=True)
        print(f"Created html directory {self.html_save_dir}")

        # Create images directory
        self.images_dir = os.path.join(md_save_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        print(f"Created images directory {self.images_dir}")

        self.keywords = ["about", "archive", "podcast"]
        self.post_urls = self.get_all_post_urls()

        # Delay configuration for rate limiting
        self.delay_range = delay_range

    def get_all_post_urls(self) -> list[str]:
        """Attempts to fetch URLs from sitemap.xml, falling back to feed.xml if necessary."""
        urls = self.fetch_urls_from_sitemap()
        if not urls:
            urls = self.fetch_urls_from_feed()
        return self.filter_urls(urls, self.keywords)

    def fetch_urls_from_sitemap(self) -> list[str]:
        """Fetches URLs from sitemap.xml."""
        sitemap_url = f"{self.base_substack_url}sitemap.xml"
        try:
            response = requests.get(sitemap_url, timeout=10)
            if not response.ok:
                print(f"Error fetching sitemap at {sitemap_url}: {response.status_code}")
                return []

            root = ET.fromstring(response.content)
            urls = [
                element.text
                for element in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if element.text
            ]
            print(f"Found {len(urls)} URLs in sitemap")
            return urls
        except Exception as e:
            print(f"Failed to fetch sitemap: {e}")
            return []

    def fetch_urls_from_feed(self) -> list[str]:
        """Fetches URLs from feed.xml."""
        print("Falling back to feed.xml. This will only contain up to the 22 most recent posts.")
        feed_url = f"{self.base_substack_url}feed.xml"
        try:
            response = requests.get(feed_url, timeout=10)
            if not response.ok:
                print(f"Error fetching feed at {feed_url}: {response.status_code}")
                return []

            root = ET.fromstring(response.content)
            urls: list[str] = []
            for item in root.findall(".//item"):
                link = item.find("link")
                if link is not None and link.text:
                    urls.append(link.text)
            print(f"Found {len(urls)} URLs in feed")
            return urls
        except Exception as e:
            print(f"Failed to fetch feed: {e}")
            return []

    @staticmethod
    def filter_urls(urls: list[str], keywords: list[str]) -> list[str]:
        """Filters out URLs that contain certain keywords."""
        filtered = [url for url in urls if all(keyword not in url for keyword in keywords)]
        print(f"Filtered {len(urls)} URLs to {len(filtered)} post URLs")
        return filtered

    @staticmethod
    def html_to_md(html_content: str) -> str:
        """Converts HTML to Markdown using html-to-markdown library."""

        return convert_to_markdown(
            html_content,
            heading_style="atx",
            strong_em_symbol="*",
            bullets="*+-",
            wrap=True,
            wrap_width=100,
            escape_asterisks=True,
            code_language="python",
            strip=["script", "style", "meta", "head", "button", "svg"],
        )

    @staticmethod
    async def save_to_file(filepath: str, content: str) -> None:
        """Saves content to a file asynchronously."""

        if os.path.exists(filepath):
            print(f"File already exists: {filepath}")
            return

        async with aiofiles.open(filepath, "w", encoding="utf-8") as file:
            await file.write(content)

    @staticmethod
    def md_to_html(md_content: str) -> str:
        """Converts Markdown to HTML."""
        return markdown.markdown(md_content, extensions=["extra"])

    async def save_to_html_file(self, filepath: str, content: str) -> None:
        """Saves HTML content to a file with CSS link."""

        html_dir = os.path.dirname(filepath)
        css_path = os.path.relpath("./assets/css/essay-styles.css", html_dir)
        css_path = css_path.replace("\\", "/")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Substack Post</title>
    <link rel="stylesheet" href="{css_path}">
</head>
<body>
    <main class="markdown-content">
    {content}
    </main>
</body>
</html>"""

        async with aiofiles.open(filepath, "w", encoding="utf-8") as file:
            await file.write(html_content)

    @staticmethod
    def get_filename_from_url(url: str, filetype: str = ".md") -> str:
        """Gets the filename from the URL."""

        if not filetype.startswith("."):
            filetype = f".{filetype}"
        return url.split("/")[-1] + filetype

    @staticmethod
    def combine_metadata_and_content(title: str, subtitle: str, date: str, like_count: str, content: str) -> str:
        """Combines metadata and content into Markdown format."""

        metadata = f"# {title}\n\n"
        if subtitle:
            metadata += f"## {subtitle}\n\n"
        metadata += f"**{date}**\n\n"
        metadata += f"**Likes:** {like_count}\n\n"
        return metadata + content

    async def download_image(self, img_url: str, post_title: str) -> str:
        """Download image and return local path."""
        try:
            # Clean the post title for use in filename
            safe_title = re.sub(r"[^\w\s-]", "", post_title).strip()
            safe_title = re.sub(r"[-\s]+", "-", safe_title)[:50]  # Limit length

            # Extract image extension
            parsed_url = urlparse(img_url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1] or ".jpg"

            # Create unique filename
            img_hash = str(hash(img_url))[-8:]  # Last 8 chars of hash for uniqueness
            filename = f"{safe_title}_{img_hash}{ext}"
            local_path = os.path.join(self.images_dir, filename)

            # Check if already downloaded
            if os.path.exists(local_path):
                return f"images/{filename}"

            # Download with rate limiting
            print(f"  Downloading image: {filename}")
            response = requests.get(img_url, headers={"User-Agent": USER_AGENT}, timeout=30)
            response.raise_for_status()

            # Save image
            with open(local_path, "wb") as f:
                f.write(response.content)

            # Add delay for rate limiting
            delay = random.uniform(0.5, 1.5)  # Shorter delay for images
            await asyncio.sleep(delay)

            return f"images/{filename}"
        except Exception as e:
            print(f"  Error downloading image {img_url}: {e}")
        return img_url  # Return original URL on error

    async def process_images_in_content(self, content: str, post_title: str) -> str:
        """Process all images in content and replace with local paths."""
        soup = BeautifulSoup(content, "html.parser")
        images = soup.find_all("img")

        for img in images:
            if hasattr(img, "get") and hasattr(img, "__setitem__"):  # Type guard for Tag
                src = img.get("src")  # type: ignore
                if src and isinstance(src, str):  # Type guard
                    # Make URL absolute if relative
                    if not src.startswith(("http://", "https://")):
                        src = urljoin(self.base_substack_url, src)

                    # Download image and get local path
                    local_path = await self.download_image(src, post_title)
                    img["src"] = local_path  # type: ignore

        return str(soup)

    async def extract_post_data(self, soup: BeautifulSoup, url: str) -> tuple[str, str, str, str, str]:
        """Extracts post data from BeautifulSoup object."""
        # Title extraction
        title_elem = soup.select_one("h1.post-title, h2")
        title = title_elem.text.strip() if title_elem else "Untitled"

        # Subtitle extraction
        subtitle_elem = soup.select_one("h3.subtitle")
        subtitle = subtitle_elem.text.strip() if subtitle_elem else ""

        # Date extraction - try multiple selectors
        date = "Date not found"
        date_selectors = [
            "time",
            "div.post-meta time",
            "div[class*='meta'] time",
            "div.pencraft",
        ]
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                # Try to get datetime attribute first
                date_attr = date_elem.get("datetime")
                date = str(date_attr) if date_attr else date_elem.text.strip()
                if date:
                    break

        # Like count extraction
        like_count_elem = soup.select_one("a.post-ufi-button .label")
        like_count = "0"
        if like_count_elem:
            text = like_count_elem.text.strip()
            if text.isdigit():
                like_count = text

        # Content extraction
        content_elem = soup.select_one("div.available-content")
        if not content_elem:
            content_elem = soup.select_one("article")
        content = str(content_elem) if content_elem else ""

        # Process images before converting to markdown
        print(f"Processing images for: {title}")
        content = await self.process_images_in_content(content, title)

        md = self.html_to_md(content)
        md_content = self.combine_metadata_and_content(title, subtitle, date, like_count, md)
        return title, subtitle, like_count, date, md_content

    @abstractmethod
    async def get_url_soup(self, url: str) -> BeautifulSoup | None:
        """Abstract method to get BeautifulSoup from URL."""
        raise NotImplementedError

    async def save_essays_data_to_json(self, essays_data: list[dict[str, Any]]) -> None:
        """Saves essays data to JSON file."""
        data_dir = os.path.join(JSON_DATA_DIR)
        os.makedirs(data_dir, exist_ok=True)

        json_path = os.path.join(data_dir, f"{self.writer_name}.json")
        existing_data: list[dict[str, Any]] = []

        if os.path.exists(json_path):
            async with aiofiles.open(json_path, encoding="utf-8") as file:
                content = await file.read()
                loaded_data = json.loads(content)
                if isinstance(loaded_data, list):
                    existing_data = loaded_data  # type: ignore

        # Merge with existing data
        merged_data: list[dict[str, Any]] = existing_data + [data for data in essays_data if data not in existing_data]

        async with aiofiles.open(json_path, "w", encoding="utf-8") as file:
            await file.write(json.dumps(merged_data, ensure_ascii=False, indent=4))

    async def scrape_posts(self, num_posts_to_scrape: int = 0) -> None:
        """Scrapes posts and saves them as markdown and HTML files."""
        essays_data: list[dict[str, Any]] = []
        count = 0
        total = num_posts_to_scrape if num_posts_to_scrape != 0 else len(self.post_urls)

        # Use async progress bar
        pbar = tqdm(total=total, desc="Scraping posts")

        for url in self.post_urls:
            try:
                md_filename = self.get_filename_from_url(url, filetype=".md")
                html_filename = self.get_filename_from_url(url, filetype=".html")
                md_filepath = os.path.join(self.md_save_dir, md_filename)
                html_filepath = os.path.join(self.html_save_dir, html_filename)

                if not os.path.exists(md_filepath):
                    soup = await self.get_url_soup(url)
                    if soup is None:
                        pbar.update(1)
                        continue

                    title, subtitle, like_count, date, md = await self.extract_post_data(soup, url)
                    await self.save_to_file(md_filepath, md)

                    # Convert markdown to HTML and save
                    html_content = self.md_to_html(md)
                    await self.save_to_html_file(html_filepath, html_content)

                    essays_data.append(
                        {
                            "title": title,
                            "subtitle": subtitle,
                            "like_count": like_count,
                            "date": date,
                            "file_link": md_filepath,
                            "html_link": html_filepath,
                        }
                    )

                    # Add random delay between scraping posts to be respectful to servers
                    delay = random.uniform(self.delay_range[0], self.delay_range[1])
                    print(f"Waiting {delay:.1f} seconds before next request...")
                    await asyncio.sleep(delay)

                else:
                    print(f"File already exists: {md_filepath}")
            except Exception as e:
                print(f"Error scraping post {url}: {e}")

            count += 1
            pbar.update(1)

            if num_posts_to_scrape != 0 and count >= num_posts_to_scrape:
                break

        pbar.close()

        await self.save_essays_data_to_json(essays_data)
        await generate_html_file(self.writer_name)


class PydollSubstackScraper(BaseSubstackScraper):
    """Pydoll-based Substack scraper with async support."""

    def __init__(
        self,
        base_substack_url: str,
        md_save_dir: str,
        html_save_dir: str,
        headless: bool = False,
        browser_path: str = "",
        user_agent: str = "",
        delay_range: tuple[int, int] = (1, 3),
        manual_login: bool = False,
    ):
        super().__init__(base_substack_url, md_save_dir, html_save_dir, delay_range)
        self.headless = headless
        self.browser_path = browser_path
        self.user_agent = user_agent
        self.browser = None
        self.tab = None
        self.auth_token = None
        self.is_logged_in = False
        self.manual_login = manual_login

    async def initialize_browser(self):
        """Initialize Pydoll browser with options."""
        options = ChromiumOptions()

        if self.headless:
            options.add_argument("--headless=new")

        if self.browser_path:
            options.binary_location = self.browser_path

        if self.user_agent:
            options.add_argument(f"user-agent={self.user_agent}")

        # Performance optimizations
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")

        self.browser = Chrome(options=options)
        self.tab = await self.browser.start()

        # Enable network events for monitoring
        await self.tab.enable_network_events()

        # Resource blocking temporarily disabled
        # await self.setup_resource_blocking()

    # Resource blocking temporarily disabled - imports not available in current Pydoll version
    # async def setup_resource_blocking(self):
    #     """Set up resource blocking for faster page loads."""
    #     # Block images, fonts, and media
    #     for resource_type in [ResourceType.IMAGE, ResourceType.FONT, ResourceType.MEDIA]:
    #         await self.tab.enable_fetch_events(resource_type=resource_type)
    #
    #     async def block_resources(tab, event):
    #         request_id = event["params"]["requestId"]
    #         await self.browser.fail_request(request_id, NetworkErrorReason.BLOCKED_BY_CLIENT)
    #
    #     await self.tab.on(FetchEvent.REQUEST_PAUSED, partial(block_resources, self.tab))

    async def login(self) -> None:
        """Login to Substack using Pydoll."""
        if not SUBSTACK_EMAIL or not SUBSTACK_PASSWORD:
            print("No credentials provided, skipping login")
            return

        if self.tab is None:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")

        print("Logging in to Substack...")

        # Network interception temporarily disabled - NetworkEvent not available in current Pydoll version
        # async def capture_auth_response(tab, event):
        #     response = event["params"]["response"]
        #     url = response["url"]
        #
        #     if "/api/v1/login" in url and response["status"] == 200:
        #         # Capture authentication success
        #         self.is_logged_in = True
        #         print("Login successful!")
        #
        # await self.tab.on(NetworkEvent.RESPONSE_RECEIVED, partial(capture_auth_response, self.tab))

        # Navigate to login page
        await self.tab.go_to("https://substack.com/sign-in")

        # Click "Sign in with password"
        signin_button = await self.tab.find(
            tag_name="a", class_name="login-option", text="Sign in with password", timeout=10
        )
        if signin_button:
            await signin_button.click()  # type: ignore

        # Wait for form to appear
        await asyncio.sleep(2)

        # Fill in credentials
        email_input = await self.tab.find(name="email", timeout=5)
        if email_input:
            await email_input.type_text(SUBSTACK_EMAIL, interval=0.05)  # type: ignore

        password_input = await self.tab.find(name="password", timeout=5)
        if password_input:
            await password_input.type_text(SUBSTACK_PASSWORD, interval=0.05)  # type: ignore

        # Submit form
        submit_button = await self.tab.find(tag_name="button", timeout=5)
        if submit_button:
            await submit_button.click()  # type: ignore

        # Wait for login to complete
        await asyncio.sleep(5)

        # Check for error
        error_container = await self.tab.find(id="error-container", timeout=2, raise_exc=False)
        if error_container:
            raise Exception("Login failed. Please check your credentials.")
        else:
            # Assume login successful if no error
            self.is_logged_in = True
            print("Login successful!")

    async def perform_manual_login(self) -> None:
        """Manual login mode - opens login page and waits for user to login manually."""
        if self.tab is None:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")

        print("Opening Substack login page for manual login...")
        print("You will be able to login manually in the browser window.")

        # Navigate to login page
        await self.tab.go_to("https://substack.com/sign-in")

        # Wait for page to load
        await asyncio.sleep(2)

        print("\n" + "=" * 60)
        print("MANUAL LOGIN MODE")
        print("=" * 60)
        print("1. The browser should now show the Substack login page")
        print("2. Please login manually in the browser window")
        print("3. You can use any login method (email/password, Google, etc.)")
        print("4. Once you're logged in, press Enter to continue...")
        print("=" * 60)

        # Pause for manual login
        input("Press Enter after you have successfully logged in: ")

        # Verify login by checking for common logged-in elements
        print("Verifying login status...")

        # Check for user menu or profile indicators
        user_menu = await self.tab.find(class_name="user-menu", timeout=3, raise_exc=False)
        # For now, just check for user menu as profile/settings links might vary
        profile_link = None
        settings_link = None

        if user_menu or profile_link or settings_link:
            self.is_logged_in = True
            print("✓ Login verification successful!")
        else:
            print("⚠ Warning: Could not verify login status. Continuing anyway...")
            print("If you encounter access issues with premium content, please try again.")
            self.is_logged_in = True  # Assume successful for manual mode

    async def get_url_soup(self, url: str) -> BeautifulSoup | None:
        """Get BeautifulSoup from URL using Pydoll."""
        if self.tab is None:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")

        try:
            # Enable Cloudflare bypass if needed
            async with self.tab.expect_and_bypass_cloudflare_captcha():
                await self.tab.go_to(url)

            # Wait for content to load - multiple strategies for thorough loading
            print("  Waiting for page to fully load...")

            # 1. Wait for network to be idle
            await self.tab.wait_for_load_state("networkidle")  # type: ignore

            # 2. Wait for specific content indicators
            content_loaded = False
            for selector in ["div.available-content", "article", "div.post-content"]:
                content_elem = await self.tab.find(class_name=selector.replace(".", ""), timeout=5, raise_exc=False)
                if content_elem:
                    content_loaded = True
                    break

            # 3. Additional wait for dynamic content
            if content_loaded:
                await asyncio.sleep(2)  # Give extra time for images/dynamic content

            # 4. Wait for images to start loading
            await self.tab.wait_for_load_state("domcontentloaded")  # type: ignore

            # Check for paywall
            paywall = await self.tab.find(tag_name="h2", class_name="paywall-title", raise_exc=False)
            if paywall and not self.is_logged_in:
                print(f"Skipping premium article: {url}")
                return None

            # Get page source
            page_source = await self.tab.page_source
            return BeautifulSoup(page_source, "html.parser")

        except Exception as e:
            print(f"Error fetching page {url}: {e}")
            return None

    async def scrape_posts(self, num_posts_to_scrape: int = 0) -> None:
        """Override to handle browser lifecycle."""
        try:
            await self.initialize_browser()

            # Login if premium scraping is enabled
            if USE_PREMIUM or (SUBSTACK_EMAIL and SUBSTACK_PASSWORD) or self.manual_login:
                if self.manual_login:
                    await self.perform_manual_login()
                else:
                    await self.login()

            # Call parent scrape_posts
            await super().scrape_posts(num_posts_to_scrape)

        finally:
            if self.browser:
                await self.browser.stop()

    async def scrape_posts_concurrently(self, num_posts_to_scrape: int = 0, max_concurrent: int = 3) -> None:
        """Scrape posts concurrently for better performance."""
        try:
            await self.initialize_browser()

            if USE_PREMIUM or (SUBSTACK_EMAIL and SUBSTACK_PASSWORD) or self.manual_login:
                if self.manual_login:
                    await self.perform_manual_login()
                else:
                    await self.login()

            essays_data: list[dict[str, Any]] = []
            urls_to_scrape = self.post_urls[:num_posts_to_scrape] if num_posts_to_scrape else self.post_urls

            # Process in batches
            for i in range(0, len(urls_to_scrape), max_concurrent):
                batch = urls_to_scrape[i : i + max_concurrent]
                tasks: list[Any] = []

                for url in batch:
                    task = self.scrape_single_post(url)
                    tasks.append(task)

                # Wait for batch to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, dict):
                        essays_data.append(result)  # type: ignore
                    elif isinstance(result, Exception):
                        print(f"Error in concurrent scraping: {result}")

                # Add delay between batches to be respectful to servers
                if i + max_concurrent < len(urls_to_scrape):
                    delay = random.uniform(self.delay_range[0], self.delay_range[1])
                    print(f"Batch completed. Waiting {delay:.1f} seconds before next batch...")
                    await asyncio.sleep(delay)

            await self.save_essays_data_to_json(essays_data)
            await generate_html_file(self.writer_name)

        finally:
            if self.browser:
                await self.browser.stop()

    async def scrape_single_post(self, url: str) -> dict[str, Any] | None:
        """Scrape a single post and return its data."""
        try:
            md_filename = self.get_filename_from_url(url, filetype=".md")
            html_filename = self.get_filename_from_url(url, filetype=".html")
            md_filepath = os.path.join(self.md_save_dir, md_filename)
            html_filepath = os.path.join(self.html_save_dir, html_filename)

            if os.path.exists(md_filepath):
                print(f"File already exists: {md_filepath}")
                return None

            # Create new tab for concurrent scraping
            if self.browser is None:
                raise RuntimeError("Browser not initialized")
            tab = await self.browser.new_tab()

            try:
                # Navigate to post
                await tab.go_to(url)

                # Wait for full page load
                print("  Waiting for page to fully load...")
                await tab.wait_for_load_state("networkidle")  # type: ignore

                # Wait for content to be available
                content_elem = await tab.find(class_name="available-content", timeout=10, raise_exc=False)
                if not content_elem:
                    content_elem = await tab.find(tag_name="article", timeout=5, raise_exc=False)

                # Additional wait for dynamic content
                await asyncio.sleep(2)

                # Check for paywall
                paywall = await tab.find(tag_name="h2", class_name="paywall-title", raise_exc=False)
                if paywall and not self.is_logged_in:
                    print(f"Skipping premium article: {url}")
                    return None

                # Get page source
                page_source = await tab.page_source
                soup = BeautifulSoup(page_source, "html.parser")

                title, subtitle, like_count, date, md = await self.extract_post_data(soup, url)
                await self.save_to_file(md_filepath, md)

                # Convert markdown to HTML and save
                html_content = self.md_to_html(md)
                await self.save_to_html_file(html_filepath, html_content)

                return {
                    "title": title,
                    "subtitle": subtitle,
                    "like_count": like_count,
                    "date": date,
                    "file_link": md_filepath,
                    "html_link": html_filepath,
                }

            finally:
                await tab.close()

        except Exception as e:
            print(f"Error scraping post {url}: {e}")
            return None


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape a Substack site and convert posts to Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape free posts from a Substack
  pydoll-substack2md https://example.substack.com

  # Scrape with login for premium content
  pydoll-substack2md https://example.substack.com -l

  # Manual login mode (works with any login method)
  pydoll-substack2md https://example.substack.com --manual-login

  # Scrape only 10 posts
  pydoll-substack2md https://example.substack.com -n 10

  # Run in headless mode (default is non-headless for user intervention)
  pydoll-substack2md https://example.substack.com --headless

  # Use concurrent scraping
  pydoll-substack2md https://example.substack.com --concurrent

  # Custom delay between requests (1-5 seconds)
  pydoll-substack2md https://example.substack.com --delay-min 1 --delay-max 5
""",
    )

    parser.add_argument(
        "url",
        nargs="?",
        type=str,
        help="The base URL of the Substack site to scrape",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default=BASE_MD_DIR,
        help="The directory to save scraped posts (default: substack_md_files)",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=0,
        help="Number of posts to scrape (0 = all posts)",
    )
    parser.add_argument(
        "-l",
        "--login",
        action="store_true",
        help="Login to Substack for premium content (requires SUBSTACK_EMAIL and SUBSTACK_PASSWORD in .env)",
    )
    parser.add_argument(
        "--manual-login",
        action="store_true",
        help="Open login page and pause for manual login (works with any login method)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: non-headless to allow user intervention)",
    )
    parser.add_argument(
        "--browser-path",
        type=str,
        default="",
        help="Path to Chrome/Edge browser executable",
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default="",
        help="Custom user agent string",
    )
    parser.add_argument(
        "--html-directory",
        type=str,
        default=BASE_HTML_DIR,
        help="Directory to save HTML files (default: substack_html_pages)",
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Use concurrent scraping for better performance",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum concurrent scraping tasks (default: 3)",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=1.0,
        help="Minimum delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=3.0,
        help="Maximum delay between requests in seconds (default: 3.0)",
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Use URL from args or environment
    url = args.url or BASE_SUBSTACK_URL
    if not url:
        print("Error: No Substack URL provided. Use -h for help.")
        sys.exit(1)

    # Determine if we should use premium scraping
    use_login = args.login or USE_PREMIUM or (SUBSTACK_EMAIL and SUBSTACK_PASSWORD)
    use_manual_login = args.manual_login

    # Validate manual login with headless mode
    if use_manual_login and (args.headless or HEADLESS):
        print("Error: Manual login mode cannot be used with headless mode")
        print("Either remove --manual-login or remove --headless")
        sys.exit(1)

    # Validate delay parameters
    if args.delay_min > args.delay_max:
        print("Error: --delay-min cannot be greater than --delay-max")
        sys.exit(1)

    print(f"Scraping: {url}")
    print(f"Login enabled: {use_login}")
    print(f"Manual login mode: {use_manual_login}")
    print(f"Headless mode: {args.headless or HEADLESS}")
    print(f"Delay range: {args.delay_min}-{args.delay_max} seconds")

    scraper = PydollSubstackScraper(
        base_substack_url=url,
        md_save_dir=args.directory,
        html_save_dir=args.html_directory,
        headless=args.headless or HEADLESS,
        browser_path=args.browser_path or BROWSER_PATH,
        user_agent=args.user_agent or USER_AGENT,
        delay_range=(args.delay_min, args.delay_max),
        manual_login=use_manual_login,
    )

    if args.concurrent:
        await scraper.scrape_posts_concurrently(
            num_posts_to_scrape=args.number or NUM_POSTS_TO_SCRAPE, max_concurrent=args.max_concurrent
        )
    else:
        await scraper.scrape_posts(num_posts_to_scrape=args.number or NUM_POSTS_TO_SCRAPE)

    print("Scraping completed!")


def run():
    """Entry point for command line execution."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
