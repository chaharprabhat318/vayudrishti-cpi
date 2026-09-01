"""
VayuDrishti Abstract Base Scraper
Provides resilient HTTP clients, stealth headers, user-agent rotation, and error handling.
"""
import random
import time
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
]

class BasePortalScraper(ABC):
    def __init__(self, portal_name: str, base_url: str):
        self.portal_name = portal_name
        self.base_url = base_url
        self.client = httpx.Client(
            timeout=12.0,
            headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,hi;q=0.8"
            }
        )

    def get_random_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.base_url
        }

    @abstractmethod
    def fetch_quotes_for_route(self, origin: str, destination: str, lead_time_days: int) -> List[Dict[str, Any]]:
        pass
