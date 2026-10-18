"""
Pinkbike BuySell HTML parser.

Parses both search result pages (listing summaries) and individual
listing detail pages into structured data objects.

Calibrated against real Pinkbike HTML as of March 2026.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup, Tag

from src.constants import CONDITION_SCORES, EXCHANGE_TO_CAD

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ListingSummary:
    """Listing data from a search results page."""
    pinkbike_id: str
    title: str
    price: float = 0.0
    currency: str = "CAD"
    category: str = ""
    condition: Optional[str] = None
    seller_location: Optional[str] = None
    url: str = ""
    thumbnail_url: Optional[str] = None
    is_boosted: bool = False
    photo_count: int = 0
    frame_size: Optional[str] = None
    wheel_size: Optional[str] = None
    material: Optional[str] = None
    front_travel: Optional[int] = None
    rear_travel: Optional[int] = None
    description_preview: str = ""
    seller_username: str = ""


@dataclass
class ListingDetail:
    """Full listing data from a detail page."""
    pinkbike_id: str
    title: str
    price: float = 0.0
    currency: str = "CAD"
    original_price: float = 0.0
    category: str = ""
    condition: Optional[str] = None
    seller_type: Optional[str] = None
    seller_location: str = ""
    seller_country: str = ""
    seller_region: str = ""
    seller_city: str = ""
    seller_username: str = ""
    seller_rating: Optional[float] = None
    frame_size: Optional[str] = None
    wheel_size: Optional[str] = None
    material: Optional[str] = None
    front_travel: Optional[int] = None
    rear_travel: Optional[int] = None
    description: str = ""
    photo_urls: list = field(default_factory=list)
    url: str = ""
    date_posted: Optional[str] = None
    is_sold: bool = False
    is_boosted: bool = False
    views: Optional[int] = None


# ---------------------------------------------------------------------------
# Price parsing
# ---------------------------------------------------------------------------

_PRICE_PATTERN = re.compile(r'[\d,]+\.?\d*')
_CURRENCY_PATTERN = re.compile(r'\b(CAD|USD|EUR|GBP|AUD)\b', re.IGNORECASE)
_CURRENCY_SYMBOL_MAP = {
    "C$": "CAD", "CA$": "CAD",
    "US$": "USD",
    "€": "EUR",
    "£": "GBP",
    "A$": "AUD",
}


def parse_price(text: str) -> tuple[float, str]:
    """
    Parse a price string into (amount, currency).

    Handles: "$4,500 CAD", "C$3,200", "€2,800", "$1,500", "£900 GBP",
             "$3800 USD", "$3,800 USD"
    Returns: (4500.0, "CAD") etc.
    """
    if not text:
        return 0.0, "USD"

    text = text.strip()

    # Detect currency from code
    currency = "USD"  # default
    cur_match = _CURRENCY_PATTERN.search(text)
    if cur_match:
        currency = cur_match.group(1).upper()
    else:
        # Check for symbol prefixes
        for symbol, cur_code in _CURRENCY_SYMBOL_MAP.items():
            if symbol in text:
                currency = cur_code
                break

    # Extract numeric value
    num_match = _PRICE_PATTERN.search(text)
    if num_match:
        num_str = num_match.group().replace(",", "")
        try:
            price = float(num_str)
        except ValueError:
            price = 0.0
    else:
        price = 0.0

    return price, currency


def normalize_price_to_cad(price: float, currency: str) -> float:
    """Convert any currency to CAD."""
    rate = EXCHANGE_TO_CAD.get(currency, 1.0)
    return round(price * rate, 2)


# ---------------------------------------------------------------------------
# Listing ID pattern
# ---------------------------------------------------------------------------

_LISTING_ID_PATTERN = re.compile(r'/buysell/(\d+)/?')


# ---------------------------------------------------------------------------
# Search results page parser
# ---------------------------------------------------------------------------

class PinkbikeParser:
    """
    Parse Pinkbike BuySell HTML pages.

    Real Pinkbike HTML structure (as of March 2026):
    - Search page: div.bsitem containers, each with table-based layout
    - Detail page: h1.buysell-title, div.buysell-price, div.detailsgrid, etc.
    """

    # ------------------------------------------------------------------
    # Search results page
    # ------------------------------------------------------------------

    @classmethod
    def parse_search_page(cls, html: str, category: str = "") -> list[ListingSummary]:
        """
        Parse a BuySell search results page.

        Args:
            html: Raw HTML string
            category: Category name for context

        Returns:
            List of ListingSummary objects
        """
        soup = BeautifulSoup(html, "lxml")
        listings = []

        # Primary strategy: div.bsitem containers (real Pinkbike structure)
        containers = soup.find_all("div", class_="bsitem")
        if not containers:
            # Also try without exact match
            containers = soup.find_all("div", class_=lambda c: c and "bsitem" in c)

        if containers:
            logger.debug(f"Found {len(containers)} bsitem containers")
            for elem in containers:
                try:
                    summary = cls._parse_bsitem(elem, category)
                    if summary and summary.pinkbike_id:
                        listings.append(summary)
                except Exception as e:
                    logger.warning(f"Failed to parse bsitem: {e}")
        else:
            # Fallback: find all links to /buysell/DIGITS/
            listings = cls._fallback_search_parse(soup, category)

        if not listings:
            cls._log_discovery(soup, "search")

        logger.info(f"Parsed {len(listings)} listings from search page [{category}]")
        return listings

    @classmethod
    def _parse_bsitem(cls, elem: Tag, category: str) -> Optional[ListingSummary]:
        """
        Parse a single div.bsitem element.

        Real structure:
            <div class="bsitem [boosted]" id="csidNNNNNNN">
              <table>
                <tr class="bsitem-table">
                  <td> (thumbnail)
                    <ul class="uPhotoSmall"><li class="uImage"><a href="/buysell/ID/"><img></a></li></ul>
                    <span class="fgrey">N photos</span>
                  </td>
                  <td> (details)
                    <div class="bsitem-title">
                      <a href="/buysell/ID/" style="...">TITLE</a>
                      <br/>Category Name
                      <div class="itemdetail"><b>Condition :</b> ...</div>
                      <div class="itemdetail"><b>Frame Size :</b> ...</div>
                      ...
                    </div>
                    <table class="bsitem-details">
                      <tr><td>LOCATION</td></tr>
                      <tr><td class="bsitem-price"><b>$PRICE CUR</b></td></tr>
                      <tr><td><b>Seller:</b> <a>username</a></td></tr>
                      <tr><td class="bsitem-description">...</td></tr>
                    </table>
                  </td>
                </tr>
              </table>
            </div>
        """
        # --- Listing ID ---
        # Try the div id attribute first (format: "csidNNNNNNN")
        elem_id = elem.get("id", "")
        pinkbike_id = ""
        if elem_id.startswith("csid"):
            pinkbike_id = elem_id.replace("csid", "")

        # Find the title link (first link with /buysell/DIGITS/)
        title_link = None
        for a_tag in elem.find_all("a", href=True):
            href = a_tag.get("href", "")
            id_match = _LISTING_ID_PATTERN.search(href)
            if id_match:
                if not pinkbike_id:
                    pinkbike_id = id_match.group(1)
                # The title link is the one with visible text (not just an image wrapper)
                text = a_tag.get_text(strip=True)
                if text and len(text) > 3 and text != "[Read More]":
                    title_link = a_tag
                    break

        if not pinkbike_id:
            return None

        # --- Title ---
        title = ""
        title_div = elem.find("div", class_="bsitem-title")
        if title_div:
            # The title is in the first <a> inside bsitem-title
            title_a = title_div.find("a")
            if title_a:
                title = title_a.get_text(strip=True)
        if not title and title_link:
            title = title_link.get_text(strip=True)

        # --- URL ---
        url = f"https://www.pinkbike.com/buysell/{pinkbike_id}/"

        # --- Price ---
        price, currency = 0.0, "USD"
        price_td = elem.find("td", class_="bsitem-price")
        if price_td:
            price, currency = parse_price(price_td.get_text(strip=True))

        # --- Item details (condition, frame size, wheel size, etc.) ---
        condition = None
        frame_size = None
        wheel_size = None
        material = None
        front_travel = None
        rear_travel = None

        for detail_div in elem.find_all("div", class_="itemdetail"):
            text = detail_div.get_text(strip=True)
            text_lower = text.lower()

            if "condition" in text_lower:
                # Extract value after the label
                condition = cls._extract_detail_value(detail_div)
            elif "frame size" in text_lower:
                frame_size = cls._extract_detail_value(detail_div)
            elif "wheel size" in text_lower:
                wheel_size = cls._extract_detail_value(detail_div)
            elif "material" in text_lower:
                material = cls._extract_detail_value(detail_div)
            elif "front travel" in text_lower:
                val = cls._extract_detail_value(detail_div)
                front_travel = cls._parse_travel_mm(val)
            elif "rear travel" in text_lower:
                val = cls._extract_detail_value(detail_div)
                rear_travel = cls._parse_travel_mm(val)

        # Normalize condition to match our scoring keys
        if condition:
            condition = cls._normalize_condition(condition)

        # --- Location ---
        location = None
        # Location is in bsitem-details table, in a td with a flag image
        flag_img = elem.find("img", class_=lambda c: c and "flag" in str(c))
        if flag_img:
            parent_td = flag_img.find_parent("td")
            if parent_td:
                location = parent_td.get_text(strip=True)

        # --- Seller username ---
        seller_username = ""
        for a_tag in elem.find_all("a", href=True):
            href = a_tag.get("href", "")
            if "/u/" in href and "/buysell/" in href:
                seller_username = a_tag.get_text(strip=True)
                break

        # --- Boosted ---
        classes = " ".join(elem.get("class", []))
        is_boosted = "boosted" in classes

        # --- Thumbnail ---
        thumbnail = None
        img = elem.find("img", alt=lambda a: a and "buysell" in str(a).lower())
        if not img:
            # Try any img inside uPhotoSmall
            photo_li = elem.find("li", class_="uImage")
            if photo_li:
                img = photo_li.find("img")
        if img:
            thumbnail = img.get("src") or img.get("data-src")

        # --- Photo count ---
        photo_count = 0
        fgrey = elem.find("span", class_="fgrey")
        if fgrey:
            count_match = re.search(r'(\d+)\s*photo', fgrey.get_text(strip=True))
            if count_match:
                photo_count = int(count_match.group(1))

        # --- Description preview ---
        desc_preview = ""
        desc_td = elem.find("td", class_="bsitem-description")
        if desc_td:
            desc_preview = desc_td.get_text(strip=True)
            # Remove "[Read More]" suffix
            desc_preview = re.sub(r'\[Read More\]\s*$', '', desc_preview).strip()

        return ListingSummary(
            pinkbike_id=pinkbike_id,
            title=title,
            price=price,
            currency=currency,
            category=category,
            condition=condition,
            seller_location=location,
            url=url,
            thumbnail_url=thumbnail,
            is_boosted=is_boosted,
            photo_count=photo_count,
            frame_size=frame_size,
            wheel_size=wheel_size,
            material=material,
            front_travel=front_travel,
            rear_travel=rear_travel,
            description_preview=desc_preview,
            seller_username=seller_username,
        )

    @staticmethod
    def _extract_detail_value(div: Tag) -> str:
        """
        Extract value from an itemdetail div.
        Structure: <div class="itemdetail"><b>Label :</b> Value</div>
        """
        # Get all text, remove the bold label part
        bold = div.find("b")
        if bold:
            label_text = bold.get_text(strip=True)
            full_text = div.get_text(strip=True)
            # Value is everything after the label
            value = full_text[len(label_text):].strip()
            # Remove leading colon/dash
            value = re.sub(r'^[:\-\s]+', '', value).strip()
            return value
        return div.get_text(strip=True)

    @staticmethod
    def _normalize_condition(raw: str) -> Optional[str]:
        """
        Map Pinkbike condition strings to our scoring keys.
        PB uses: "New", "Excellent - Lightly Ridden", "Good - Some Wear",
                 "Fair - Cosmetic Damage or Functional Issue"
        We use:  "New", "Excellent", "Good", "Fair"
        """
        raw_lower = raw.lower()
        if "new" in raw_lower:
            return "New"
        elif "excellent" in raw_lower:
            return "Excellent"
        elif "good" in raw_lower:
            return "Good"
        elif "fair" in raw_lower:
            return "Fair"
        return raw

    @classmethod
    def _fallback_search_parse(cls, soup: BeautifulSoup,
                                category: str) -> list[ListingSummary]:
        """
        Last-resort parser: find ALL links matching /buysell/DIGITS/
        and extract what we can.
        """
        listings = []
        seen_ids = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "")
            id_match = _LISTING_ID_PATTERN.search(href)
            if not id_match:
                continue

            pid = id_match.group(1)
            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            title = a_tag.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            url = href if href.startswith("http") else f"https://www.pinkbike.com{href}"

            listings.append(ListingSummary(
                pinkbike_id=pid,
                title=title,
                price=0.0,
                currency="CAD",
                category=category,
                url=url,
            ))

        return listings

    # ------------------------------------------------------------------
    # Individual listing detail page
    # ------------------------------------------------------------------

    @classmethod
    def parse_detail_page(cls, html: str,
                          pinkbike_id: str = "") -> Optional[ListingDetail]:
        """
        Parse an individual listing's detail page.

        Real structure:
            <h1 class="buysell-title">TITLE</h1>
            <div class="buysell-price">$PRICE CUR</div>
            <div class="detailsgrid">
              <div><b>Category:</b> ...</div>
              <div><b>Condition:</b> ...</div>
              ...
            </div>
            <div class="description">FULL DESCRIPTION</div>
            <div class="buysell-profileinfo">SELLER INFO</div>
        """
        soup = BeautifulSoup(html, "lxml")

        # --- Listing ID ---
        if not pinkbike_id:
            pinkbike_id = cls._extract_detail_id(soup)
        if not pinkbike_id:
            logger.warning("Could not extract listing ID from detail page")
            return None

        # --- Title ---
        title = ""
        title_el = soup.find("h1", class_="buysell-title")
        if title_el:
            title = title_el.get_text(strip=True)
        else:
            # Fallback
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

        # --- Price ---
        price, currency = 0.0, "CAD"
        price_el = soup.find("div", class_="buysell-price")
        if price_el:
            price, currency = parse_price(price_el.get_text(strip=True))

        # --- Details grid ---
        specs = {}
        details_grid = soup.find("div", class_="detailsgrid")
        if details_grid:
            for div in details_grid.find_all("div", recursive=False):
                bold = div.find("b")
                if bold:
                    key = bold.get_text(strip=True).rstrip(":").strip().lower()
                    full_text = div.get_text(strip=True)
                    value = full_text[len(bold.get_text(strip=True)):].strip()
                    value = re.sub(r'^[:\s]+', '', value).strip()
                    specs[key] = value

        # --- Condition ---
        condition = cls._normalize_condition(specs.get("condition", ""))
        if not condition:
            for label in CONDITION_SCORES.keys():
                if label.lower() in soup.get_text().lower():
                    condition = label
                    break

        # --- Description ---
        description = ""
        desc_el = soup.find("div", class_="description")
        if desc_el:
            description = desc_el.get_text(separator="\n", strip=True)

        # --- Seller info ---
        # Real structure: div.buysell-profileinfo contains:
        #   <a href="/u/USERNAME/buysell/" rel="author">USERNAME</a>
        #   <span class="f11">Member since ...<br/><img flag/>City, State, Country</span>
        seller_username = ""
        seller_location = ""

        profile_el = soup.find("div", class_=lambda c: c and "buysell-profileinfo" in str(c))
        if profile_el:
            # Username from author link
            user_link = profile_el.find("a", rel="author")
            if not user_link:
                user_link = profile_el.find("a", href=lambda h: h and "/u/" in h)
            if user_link:
                seller_username = user_link.get_text(strip=True)

            # Location from f11 span (after flag image)
            f11_span = profile_el.find("span", class_="f11")
            if f11_span:
                # Location text is after the flag image, get all text
                span_text = f11_span.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in span_text.split("\n") if l.strip()]
                # Location is typically the last line (after "Member since ...")
                for line in lines:
                    if "," in line and "member" not in line.lower():
                        seller_location = line
                        break

        # Parse location into components
        seller_country, seller_region, seller_city = cls._parse_location(seller_location)

        # --- Photos ---
        photo_urls = []
        # Images are lazy-loaded in buysell-images-container
        img_container = soup.find("div", class_="buysell-images-container")
        if img_container:
            for img in img_container.find_all("img"):
                src = img.get("src") or img.get("data-src") or img.get("data-lazy")
                if src and src not in photo_urls and "pinkbike.org" in src:
                    photo_urls.append(src)
        # Also check for thumbnail images
        for thumb in soup.find_all("img", class_="buysell-thumbnailimage"):
            src = thumb.get("src") or thumb.get("data-src")
            if src and src not in photo_urls:
                photo_urls.append(src)

        # --- Status banner (dates, views, sold) ---
        # Real structure: div.buysell-status-banner contains:
        #   "Available as of Xh ago  Posted: 3 days ago  Reposted: ...  Views: 95  Watchers: 0"
        date_posted = None
        views = None
        is_sold = False

        status_banner = soup.find("div", class_="buysell-status-banner")
        if status_banner:
            banner_text = status_banner.get_text(strip=True)
            # Check sold status
            if "sold" in banner_text.lower():
                is_sold = True
            # Extract views
            views_match = re.search(r'Views:\s*(\d[\d,]*)', banner_text)
            if views_match:
                views = int(views_match.group(1).replace(",", ""))
            # Extract posted date
            posted_match = re.search(r'Posted:\s*(.+?)(?:Reposted|Views|Watchers|$)',
                                     banner_text)
            if posted_match:
                date_posted = posted_match.group(1).strip()

        return ListingDetail(
            pinkbike_id=pinkbike_id,
            title=title,
            price=price,
            currency=currency,
            original_price=price,
            category=specs.get("category", ""),
            condition=condition,
            seller_type=specs.get("seller type"),
            seller_location=seller_location,
            seller_country=seller_country,
            seller_region=seller_region,
            seller_city=seller_city,
            seller_username=seller_username,
            seller_rating=None,
            frame_size=specs.get("frame size"),
            wheel_size=specs.get("wheel size"),
            material=specs.get("material"),
            front_travel=cls._parse_travel_mm(specs.get("front travel")),
            rear_travel=cls._parse_travel_mm(specs.get("rear travel")),
            description=description,
            photo_urls=photo_urls,
            url=f"https://www.pinkbike.com/buysell/{pinkbike_id}/",
            date_posted=date_posted,
            is_sold=is_sold,
            views=views,
        )

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    @classmethod
    def has_next_page(cls, html: str) -> bool:
        """Check if the search results page has a next page link."""
        soup = BeautifulSoup(html, "lxml")
        # Pinkbike uses <a rel="next"> inside paging-nav-c3
        if soup.find("a", rel="next"):
            return True
        # Also check for "Next" text in paging
        paging = soup.find("div", class_="paging-nav-c3")
        if paging:
            next_link = paging.find("a", string=lambda s: s and "Next" in s)
            if next_link:
                return True
        return False

    @classmethod
    def get_total_pages(cls, html: str) -> Optional[int]:
        """Extract total page count from pagination."""
        soup = BeautifulSoup(html, "lxml")
        # Pinkbike pagination: <ul class="paging-middle"> with <li> page numbers
        paging = soup.find("ul", class_="paging-middle")
        if paging:
            numbers = []
            for li in paging.find_all("li"):
                text = li.get_text(strip=True)
                if text.isdigit():
                    numbers.append(int(text))
            if numbers:
                return max(numbers)

        # Fallback: look in paging-nav-c3 for all page number links
        paging_div = soup.find("div", class_="paging-nav-c3")
        if paging_div:
            numbers = []
            for a in paging_div.find_all("a"):
                text = a.get_text(strip=True)
                if text.isdigit():
                    numbers.append(int(text))
            if numbers:
                return max(numbers)

        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _extract_detail_id(cls, soup: BeautifulSoup) -> str:
        """Extract listing ID from a detail page."""
        # Try canonical URL
        canonical = soup.select_one("link[rel='canonical']")
        if canonical:
            m = _LISTING_ID_PATTERN.search(canonical.get("href", ""))
            if m:
                return m.group(1)

        # Try og:url meta
        og_url = soup.select_one("meta[property='og:url']")
        if og_url:
            m = _LISTING_ID_PATTERN.search(og_url.get("content", ""))
            if m:
                return m.group(1)

        # Try data attributes
        for elem in soup.find_all(attrs={"data-id": True}):
            val = elem.get("data-id", "")
            if val.isdigit():
                return val

        return ""

    @staticmethod
    def _parse_travel_mm(text: Optional[str]) -> Optional[int]:
        """Extract travel in mm from text like '170 mm' or '170mm'."""
        if not text:
            return None
        match = re.search(r'(\d+)\s*(?:mm)?', text)
        if match:
            val = int(match.group(1))
            if 50 <= val <= 250:  # sanity check for travel range
                return val
        return None

    @staticmethod
    def _parse_location(location: str) -> tuple[str, str, str]:
        """
        Parse location string into (country, region, city).
        Handles: "Miami, Florida, United States" → ("United States", "Florida", "Miami")
        """
        if not location:
            return "", "", ""

        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 3:
            return parts[-1], parts[-2], parts[0]
        elif len(parts) == 2:
            return parts[-1], "", parts[0]
        else:
            return parts[0], "", ""

    @classmethod
    def _log_discovery(cls, soup: BeautifulSoup, page_type: str):
        """
        Log HTML structure when no selectors match.
        Helps debug parsing issues.
        """
        logger.warning(f"No selectors matched for {page_type} page. "
                       "Entering discovery mode.")

        body = soup.find("body")
        if body:
            children = body.find_all(True, recursive=False)
            tags = [f"{c.name}.{'.'.join(c.get('class', []))}" for c in children[:20]]
            logger.info(f"Body children: {tags}")

        keywords = ["buysell", "listing", "product", "item", "ad", "result", "bsitem"]
        for elem in soup.find_all(True, {"class": True}):
            classes = " ".join(elem.get("class", []))
            if any(kw in classes.lower() for kw in keywords):
                logger.info(f"Discovery: <{elem.name} class='{classes}'>")
