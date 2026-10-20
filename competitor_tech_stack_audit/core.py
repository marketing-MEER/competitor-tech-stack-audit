"""Side-by-side technical SEO profile of several domains.

For each domain: HTTPS and redirects, robots.txt (incl. AI crawlers), llms.txt,
XML sitemap, CMS / framework / CDN, structured data, hreflang, canonical,
mobile viewport, page weight, response time, security headers and image
formats. Optional: Google PageSpeed Insights scores (free API).
"""
import json
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup

USER_AGENT = "competitor-tech-stack-audit/1.0 (+https://github.com/marketing-MEER/competitor-tech-stack-audit)"
PSI = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot",
               "Google-Extended", "CCBot", "Applebot-Extended", "Bytespider"]

# (label, where, pattern): where = html | header | cookie
SIGNATURES = [
    ("WordPress", "html", r"wp-content|wp-includes|<meta[^>]+generator[^>]+WordPress"),
    ("Shopify", "html", r"cdn\.shopify\.com|Shopify\.theme"),
    ("Wix", "html", r"static\.wixstatic\.com|<meta[^>]+generator[^>]+Wix"),
    ("Squarespace", "html", r"static1\.squarespace\.com|Squarespace"),
    ("Webflow", "html", r"webflow\.(js|com)|data-wf-site"),
    ("HubSpot CMS", "html", r"hs-scripts\.com|hubspot\.net/hub|<meta[^>]+generator[^>]+HubSpot"),
    ("Drupal", "html", r"Drupal\.settings|/sites/default/files|<meta[^>]+generator[^>]+Drupal"),
    ("Joomla", "html", r"<meta[^>]+generator[^>]+Joomla"),
    ("Ghost", "html", r"<meta[^>]+generator[^>]+Ghost"),
    ("Next.js", "html", r"__NEXT_DATA__|/_next/static"),
    ("Nuxt", "html", r"__NUXT__|/_nuxt/"),
    ("Gatsby", "html", r"___gatsby"),
    ("Framer", "html", r"framerusercontent\.com|<meta[^>]+generator[^>]+Framer"),
    ("Magento", "html", r"Magento|mage/cookies"),
]
CDNS = [("Cloudflare", r"cloudflare"), ("Fastly", r"fastly"), ("Akamai", r"akamai"), ("Vercel", r"vercel"),
        ("Netlify", r"netlify"), ("Amazon CloudFront", r"cloudfront"), ("Google Cloud", r"\bgws\b|google"),
        ("Bunny CDN", r"bunny"), ("KeyCDN", r"keycdn")]


def base_url(domain: str) -> str:
    domain = domain.strip().rstrip("/")
    return domain if domain.startswith("http") else f"https://{domain}"


def get(session, url, timeout=20, **kw):
    try:
        return session.get(url, timeout=timeout, **kw)
    except requests.RequestException:
        return None


def detect_cms(html: str) -> str:
    found = [label for label, _, pat in SIGNATURES if re.search(pat, html, re.I)]
    return ", ".join(found) or "unknown / custom"


def detect_cdn(headers) -> str:
    blob = " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
    found = [label for label, pat in CDNS if re.search(pat, blob)]
    return ", ".join(found) or "none detected"


def schema_types(soup) -> list[str]:
    types = set()
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            stack = [json.loads(tag.string or "")]
        except (json.JSONDecodeError, TypeError):
            continue
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack += item
            elif isinstance(item, dict):
                t = item.get("@type")
                types.update(t if isinstance(t, list) else [t] if t else [])
                stack += [v for v in item.values() if isinstance(v, (dict, list))]
    types.update(el.get("itemtype", "").rsplit("/", 1)[-1] for el in soup.find_all(attrs={"itemtype": True}))
    return sorted(t for t in map(str, types) if t)


def ai_crawler_rules(robots_txt: str, home: str) -> dict:
    rp = RobotFileParser()
    rp.parse(robots_txt.splitlines())
    return {bot: ("allowed" if rp.can_fetch(bot, home) else "blocked") for bot in AI_CRAWLERS}


def pagespeed(url: str, key: str | None, session) -> dict:
    params = {"url": url, "strategy": "mobile", "category": "performance"}
    if key:
        params["key"] = key
    resp = get(session, PSI, timeout=120, params=params)
    empty = {"psi_mobile_performance": None, "lcp_s": None, "cls": None, "inp_ms": None}
    if resp is None:
        return {**empty, "psi_note": "PageSpeed API did not respond"}
    if resp.status_code == 429:
        return {**empty, "psi_note": "PageSpeed quota exceeded: add a free API key with --psi-key"}
    if resp.status_code != 200:
        return {**empty, "psi_note": f"PageSpeed API error {resp.status_code}"}
    data = resp.json()
    audits = data.get("lighthouseResult", {}).get("audits", {})
    field = data.get("loadingExperience", {}).get("metrics", {})
    score = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score")
    return {
        "psi_mobile_performance": round(score * 100) if score is not None else None,
        "lcp_s": round(audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000, 2) or None,
        "cls": round(audits.get("cumulative-layout-shift", {}).get("numericValue", 0), 3),
        "inp_ms": field.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile"),
        "psi_note": "ok",
    }


def audit_domain(domain: str, session=None, psi: bool = False, psi_key: str | None = None) -> dict:
    session = session or requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    home = base_url(domain)
    host = urlparse(home).netloc
    row = {"domain": host}

    http = get(session, f"http://{host}/", allow_redirects=True)
    row["http_redirects_to_https"] = bool(http is not None and http.url.startswith("https://"))

    start = time.perf_counter()
    resp = get(session, home, allow_redirects=True)
    row["response_ms"] = round((time.perf_counter() - start) * 1000)
    if resp is None:
        row["status"] = "unreachable"
        return row
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")
    final = resp.url
    row.update({
        "status": resp.status_code,
        "final_url": final,
        "https": final.startswith("https://"),
        "redirect_hops": len(resp.history),
        "html_kb": round(len(resp.content) / 1024, 1),
        "compression": resp.headers.get("Content-Encoding", "none"),
        "server": resp.headers.get("Server", ""),
        "cms_framework": detect_cms(html),
        "cdn": detect_cdn(resp.headers),
        "hsts": "strict-transport-security" in {k.lower() for k in resp.headers},
    })

    canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
    viewport = soup.find("meta", attrs={"name": "viewport"})
    robots_meta = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "robots"})
    hreflangs = soup.find_all("link", rel=lambda v: v and "alternate" in v, hreflang=True)
    imgs = [i.get("src", "") or i.get("data-src", "") for i in soup.find_all("img")]
    sources = [s.get("type", "") for s in soup.find_all("source")]
    types = schema_types(soup)
    row.update({
        "title_length": len(soup.title.get_text(strip=True)) if soup.title else 0,
        "canonical": urljoin(final, canonical["href"]) if canonical and canonical.get("href") else "",
        "mobile_viewport": bool(viewport and "width=device-width" in viewport.get("content", "")),
        "noindex_home": bool(robots_meta and "noindex" in robots_meta.get("content", "").lower()),
        "hreflang_tags": len(hreflangs),
        "schema_types": ", ".join(types),
        "schema_count": len(types),
        "has_organization_schema": any(t in ("Organization", "Corporation", "LocalBusiness") for t in types),
        "scripts": len(soup.find_all("script", src=True)),
        "images": len(imgs),
        "modern_images": sum(1 for s in imgs if re.search(r"\.(webp|avif)(\?|$)", s, re.I))
                         + sum(1 for t in sources if t in ("image/webp", "image/avif")),
        "open_graph": bool(soup.find("meta", property=re.compile(r"^og:"))),
    })

    robots = get(session, urljoin(final, "/robots.txt"))
    robots_txt = robots.text if robots is not None and robots.status_code == 200 else ""
    row["robots_txt"] = bool(robots_txt)
    sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots_txt)
    if not sitemaps:
        sm = get(session, urljoin(final, "/sitemap.xml"))
        sitemaps = [sm.url] if sm is not None and sm.status_code == 200 and "<" in sm.text[:200] else []
    row["xml_sitemap"] = bool(sitemaps)
    row["sitemap_url"] = sitemaps[0] if sitemaps else ""
    llms = get(session, urljoin(final, "/llms.txt"))
    row["llms_txt"] = bool(llms is not None and llms.status_code == 200 and "<html" not in llms.text[:500].lower())
    rules = ai_crawler_rules(robots_txt, final)
    row["ai_crawlers_blocked"] = sum(v == "blocked" for v in rules.values())
    row.update({f"ai_{bot}": rule for bot, rule in rules.items()})

    if psi:
        row.update(pagespeed(final, psi_key, session))
    return row


# Checks scored in the scorecard: (column, label, pass test). Based on the factors the NP data
# says still matter for AI search: speed, mobile, structured data, sitemaps, HTTPS.
CHECKS = [
    ("https", "Serves HTTPS", lambda v: v is True),
    ("http_redirects_to_https", "HTTP redirects to HTTPS", lambda v: v is True),
    ("hsts", "HSTS header", lambda v: v is True),
    ("mobile_viewport", "Mobile viewport", lambda v: v is True),
    ("xml_sitemap", "XML sitemap", lambda v: v is True),
    ("robots_txt", "robots.txt", lambda v: v is True),
    ("canonical", "Canonical on homepage", lambda v: bool(v)),
    ("schema_count", "Structured data", lambda v: (v or 0) > 0),
    ("has_organization_schema", "Organization schema", lambda v: v is True),
    ("llms_txt", "llms.txt", lambda v: v is True),
    ("open_graph", "Open Graph tags", lambda v: v is True),
    ("compression", "Compression (gzip/br)", lambda v: v not in (None, "", "none")),
    ("response_ms", "Homepage under 800 ms", lambda v: v is not None and v < 800),
    ("redirect_hops", "At most 1 redirect", lambda v: v is not None and v <= 1),
]


def scorecard(rows: list[dict]) -> pd.DataFrame:
    out = []
    for col, label, test in CHECKS:
        line = {"check": label}
        for r in rows:
            line[r["domain"]] = "✅" if test(r.get(col)) else "❌"
        out.append(line)
    df = pd.DataFrame(out)
    totals = {"check": "Score"}
    for r in rows:
        totals[r["domain"]] = f'{(df[r["domain"]] == "✅").sum()}/{len(CHECKS)}'
    return pd.concat([df, pd.DataFrame([totals])], ignore_index=True)


def matrix(rows: list[dict]) -> pd.DataFrame:
    """Every collected field as rows, one column per domain."""
    df = pd.DataFrame(rows).set_index("domain").T
    df.index.name = "field"
    return df.reset_index().astype(str).replace({"True": "yes", "False": "no", "nan": "–", "None": "–"})


def ai_table(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{"crawler": bot, **{r["domain"]: r.get(f"ai_{bot}", "–") for r in rows}}
                         for bot in AI_CRAWLERS])
