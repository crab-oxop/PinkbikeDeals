"""
HTTP client with rate limiting and retries.

Pinkbike serves BuySell behind Cloudflare, which rejects plain HTTP clients
(requests/urllib get a 403 "Attention Required" page). This client uses the
cloudscraper library, which presents as a desktop Chrome browser and answers
Cloudflare's JavaScript check, so pages load the way they do in a browser.
Synchronous cloudscraper calls are wrapped with asyncio for the async scraper.

Personal and educational use. Check Pinkbike's terms of use before running it.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Optional

import cloudscraper

from src.config import Config

logger = logging.getLogger(__name__)


@dataclass
class RequestStats:
    """Track scraping statistics."""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    rate_limited: int = 0
    retries: int = 0
    total_bytes: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def requests_per_minute(self) -> float:
        elapsed = time.time() - self.start_time
        if elapsed <= 0:
            return 0
        return (self.total_requests / elapsed) * 60

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful / self.total_requests


class AdaptiveRateLimiter:
    """
    Adjusts request speed based on server response signals.
    Slows down on errors, gradually speeds back up on success.
    """

    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.current_delay = base_delay
        self.max_delay = max_delay
        self.consecutive_errors = 0
        self._lock = asyncio.Lock()

    async def wait(self):
        """Wait the appropriate delay with jitter."""
        jitter = random.uniform(0, self.current_delay * 0.3)
        delay = self.current_delay + jitter
        if delay > 0.01:
            await asyncio.sleep(delay)

    async def on_success(self):
        async with self._lock:
            self.consecutive_errors = 0
            # Gradually return to base speed
            self.current_delay = max(
                self.base_delay,
                self.current_delay * 0.95
            )

    async def on_rate_limit(self):
        async with self._lock:
            self.consecutive_errors += 1
            self.current_delay = min(
                self.max_delay,
                self.current_delay * 3
            )
            logger.warning(f"Rate limited. Delay now {self.current_delay:.1f}s "
                           f"(consecutive errors: {self.consecutive_errors})")

    async def on_server_error(self):
        async with self._lock:
            self.consecutive_errors += 1
            self.current_delay = min(
                self.max_delay,
                self.current_delay * 2
            )

    async def on_forbidden(self):
        async with self._lock:
            self.consecutive_errors += 1
            self.current_delay = self.max_delay
            logger.error("403 Forbidden — possible block. Delay set to maximum.")

    @property
    def should_pause(self) -> bool:
        """True if we've hit too many consecutive errors."""
        return self.consecutive_errors >= 10

    @property
    def should_warn(self) -> bool:
        return self.consecutive_errors >= 5


@dataclass
class HTTPResponse:
    """Simplified response object wrapping cloudscraper's response."""
    status_code: int
    text: str
    content: bytes
    url: str
    headers: dict

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(
                f"HTTP {self.status_code}: {self.url}",
                status_code=self.status_code,
                url=self.url,
            )


class HTTPError(Exception):
    """HTTP error with status code."""
    def __init__(self, message: str, status_code: int = 0, url: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class ScraperHTTPClient:
    """
    HTTP client for reading Pinkbike BuySell pages.

    Features:
    - Loads pages behind Cloudflare via cloudscraper (presents as desktop Chrome)
    - Concurrency control via semaphore
    - Adaptive rate limiting with jitter
    - Automatic retry with exponential backoff
    - Request statistics tracking
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()
        sc = self.config.scraper

        self._scraper: Optional[cloudscraper.CloudScraper] = None
        self._semaphore = asyncio.Semaphore(sc.max_concurrent_requests)
        self._last_request_time = 0.0
        self._global_lock = asyncio.Lock()

        self.rate_limiter = AdaptiveRateLimiter(
            base_delay=sc.min_request_delay,
            max_delay=30.0,
        )
        self.stats = RequestStats()
        self._stopped = False

    async def __aenter__(self):
        self._scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
            }
        )
        self._scraper.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._scraper:
            self._scraper.close()
            self._scraper = None

    def stop(self):
        """Signal the client to stop making requests."""
        self._stopped = True

    async def get(self, url: str, max_retries: int = None) -> HTTPResponse:
        """
        Fetch a URL with rate limiting and retries.

        Returns HTTPResponse on success.
        Raises HTTPError or RuntimeError on failure.
        """
        if self._stopped:
            raise RuntimeError("Client has been stopped")

        if self.rate_limiter.should_pause:
            raise RuntimeError(
                f"Too many consecutive errors ({self.rate_limiter.consecutive_errors}). "
                "Scraping paused. Check if Pinkbike is blocking requests."
            )

        if max_retries is None:
            max_retries = self.config.scraper.max_retries

        async with self._semaphore:
            # Enforce global minimum delay between ANY request
            async with self._global_lock:
                now = time.time()
                elapsed = now - self._last_request_time
                min_gap = self.config.scraper.min_request_delay
                if elapsed < min_gap:
                    await asyncio.sleep(min_gap - elapsed)
                self._last_request_time = time.time()

            # Adaptive rate limiter delay
            await self.rate_limiter.wait()

            # Retry loop
            last_error = None
            for attempt in range(max_retries + 1):
                if self._stopped:
                    raise RuntimeError("Client stopped during retry")

                try:
                    self.stats.total_requests += 1

                    # cloudscraper is synchronous — run in thread pool
                    loop = asyncio.get_event_loop()
                    raw_response = await loop.run_in_executor(
                        None, self._scraper.get, url
                    )

                    response = HTTPResponse(
                        status_code=raw_response.status_code,
                        text=raw_response.text,
                        content=raw_response.content,
                        url=str(raw_response.url),
                        headers=dict(raw_response.headers),
                    )

                    # Handle response codes
                    if response.status_code == 200:
                        # Extra check: make sure we didn't get a Cloudflare challenge page
                        if "Attention Required" in response.text[:500]:
                            logger.warning("Got Cloudflare challenge page despite 200")
                            self.stats.failed += 1
                            await self.rate_limiter.on_forbidden()
                            if attempt < max_retries:
                                backoff = self.config.scraper.backoff_base ** attempt * 5
                                await asyncio.sleep(backoff)
                                self.stats.retries += 1
                                continue
                            raise HTTPError(
                                f"Cloudflare challenge on {url}",
                                status_code=403, url=url,
                            )

                        self.stats.successful += 1
                        self.stats.total_bytes += len(response.content)
                        await self.rate_limiter.on_success()
                        return response

                    elif response.status_code == 429:
                        self.stats.rate_limited += 1
                        await self.rate_limiter.on_rate_limit()
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                await asyncio.sleep(float(retry_after))
                            except ValueError:
                                await asyncio.sleep(10)
                        else:
                            backoff = (self.config.scraper.backoff_base ** attempt) * 5
                            await asyncio.sleep(backoff)
                        self.stats.retries += 1
                        continue

                    elif response.status_code == 403:
                        self.stats.failed += 1
                        await self.rate_limiter.on_forbidden()
                        raise HTTPError(
                            f"403 Forbidden: {url}",
                            status_code=403, url=url,
                        )

                    elif response.status_code >= 500:
                        await self.rate_limiter.on_server_error()
                        if attempt < max_retries:
                            backoff = self.config.scraper.backoff_base ** attempt
                            logger.warning(
                                f"Server error {response.status_code} on {url}. "
                                f"Retry {attempt + 1}/{max_retries} in {backoff:.1f}s"
                            )
                            await asyncio.sleep(backoff)
                            self.stats.retries += 1
                            continue
                        else:
                            self.stats.failed += 1
                            response.raise_for_status()

                    else:
                        self.stats.failed += 1
                        response.raise_for_status()

                except (ConnectionError, TimeoutError, OSError) as e:
                    last_error = e
                    if attempt < max_retries:
                        backoff = self.config.scraper.backoff_base ** attempt
                        logger.warning(
                            f"Request error: {e}. "
                            f"Retry {attempt + 1}/{max_retries} in {backoff:.1f}s"
                        )
                        await asyncio.sleep(backoff)
                        self.stats.retries += 1
                    else:
                        self.stats.failed += 1
                        raise

            raise RuntimeError(
                f"Failed to fetch {url} after {max_retries} retries. "
                f"Last error: {last_error}"
            )

    def get_stats_summary(self) -> str:
        """Human-readable stats summary."""
        s = self.stats
        return (
            f"Requests: {s.total_requests} total, {s.successful} ok, "
            f"{s.failed} failed, {s.rate_limited} rate-limited, "
            f"{s.retries} retries | "
            f"{s.requests_per_minute:.1f} req/min | "
            f"{s.total_bytes / 1024 / 1024:.1f} MB downloaded"
        )


# Keep backward compatibility alias
AsyncHTTPClient = ScraperHTTPClient
