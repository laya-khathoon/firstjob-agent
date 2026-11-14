"""Internship search for FirstJob Agent. Real links only, never invented.

Two kinds of results:
- "live": real postings extracted just now from a site's own search page
  (currently Internshala, which serves its listings in the HTML).
- "pages": the site's own live search page for the student's keywords, so the
  student can browse current openings even when a page cannot be parsed
  (Unstop blocks bots; the AICTE portal renders with JavaScript).

Every link is checked to respond before it is shown.
"""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 6
LINK_TIMEOUT = 5
MAX_LIVE = 10
MAX_LINK_CHECKS = 14

AICTE_URL = "https://internship.aicte-india.org/internships"


def build_search_pages(keywords):
    """Real search-page URLs on each board for the student's top keywords."""
    kws = [k.strip() for k in (keywords or []) if k and k.strip()][:3]
    pages = []
    for kw in kws:
        slug = quote(kw.lower().replace(" ", "-"))
        pages.append({"site": "Internshala", "keyword": kw,
                      "url": f"https://internshala.com/internships/keywords-{slug}/"})
        pages.append({"site": "Unstop", "keyword": kw,
                      "url": f"https://unstop.com/internships?searchTerm={quote(kw)}"})
    if kws:
        pages.append({"site": "AICTE National Internship Portal",
                      "keyword": kws[0], "url": AICTE_URL})
    return pages


def link_works(url):
    """True if the URL responds without an error (HEAD first, GET fallback)."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=LINK_TIMEOUT, allow_redirects=True)
        if r.status_code < 400:
            return True
        r = requests.get(url, headers=HEADERS, timeout=LINK_TIMEOUT, stream=True)
        r.close()
        return r.status_code < 400
    except Exception:
        return False


def _fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code < 400:
            return r.text
    except Exception:
        pass
    return None


def _parse_internshala(html, keyword):
    """Pull real postings out of an Internshala search page."""
    soup = BeautifulSoup(html, "lxml")
    postings = []
    seen = set()
    for card in soup.select("div.individual_internship[data-href]"):
        link = card.select_one("a.job-title-href")
        href = link.get("href") if link else card.get("data-href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = "https://internshala.com" + href
        if href in seen:
            continue
        seen.add(href)
        company_el = card.select_one("p.company-name")
        location_el = card.select_one("div.row-1-item.locations")
        stipend_el = card.select_one("span.stipend")
        postings.append({
            "title": link.get_text(strip=True) if link else keyword,
            "company": company_el.get_text(strip=True) if company_el else "",
            "location": location_el.get_text(" ", strip=True) if location_el else "",
            "stipend": stipend_el.get_text(strip=True) if stipend_el else "",
            "skills": [s.get_text(strip=True) for s in card.select("div.job_skill")],
            "url": href,
            "site": "Internshala",
            "keyword": keyword,
        })
    return postings


def search_internships(keywords, progress=None):
    """Fetch live postings and verified search pages for the given keywords.

    Returns {"keywords": [...], "live": [...], "pages": [...]}.
    Never raises; network failures just shrink the lists.
    """
    pages = build_search_pages(keywords)

    internshala = [p for p in pages if p["site"] == "Internshala"]

    # Fetch the Internshala search pages in parallel.
    if progress:
        progress("Fetching live internships from Internshala...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        htmls = list(pool.map(_fetch, [p["url"] for p in internshala]))
    postings = []
    seen = set()
    for page, html in zip(internshala, htmls):
        if not html:
            continue
        for posting in _parse_internshala(html, page["keyword"]):
            if posting["url"] not in seen:
                seen.add(posting["url"])
                postings.append(posting)

    # Check posting links in parallel and keep the first MAX_LIVE working ones.
    if progress:
        progress("Checking posting links...")
    candidates = postings[:MAX_LINK_CHECKS]
    with ThreadPoolExecutor(max_workers=8) as pool:
        checks = list(pool.map(link_works, [p["url"] for p in candidates]))
    live = []
    for posting, ok in zip(candidates, checks):
        if ok and len(live) < MAX_LIVE:
            live.append(posting)

    # Check the board search pages in parallel.
    if progress:
        progress("Checking internship boards...")
    with ThreadPoolExecutor(max_workers=7) as pool:
        page_checks = list(pool.map(link_works, [p["url"] for p in pages]))
    working_pages = [p for p, ok in zip(pages, page_checks) if ok]

    return {"keywords": [p["keyword"] for p in pages], "live": live, "pages": working_pages}
