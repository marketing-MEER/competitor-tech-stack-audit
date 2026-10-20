<div align="center">

# 🛠️ competitor-tech-stack-audit

### Compare the technical SEO setup of your site and your competitors side by side, including AI-search readiness.

[![tests](https://github.com/marketing-MEER/competitor-tech-stack-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/marketing-MEER/competitor-tech-stack-audit/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![No API keys](https://img.shields.io/badge/API%20keys-none%20needed-brightgreen)
[![Part of SEO Toolbox](https://img.shields.io/badge/part%20of-SEO%20Toolbox-orange)](https://github.com/marketing-MEER/seo-toolbox)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Meer%20Hamza-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/meerhamza-seo)

[🚀 Quick start](#quick-start) · [⚙️ How it works](#how-it-works) · [📄 Report](#report) · [❓ FAQ](#faq) · [👤 Author](#author)

</div>

---

## 💡 What it does

"What are they running, and what do they have that we don't?" is the first question in any competitor review. Answering it by hand means checking a dozen things per site: HTTPS, sitemap, robots.txt, schema, CMS, CDN, hreflang and so on.

`competitor-tech-stack-audit` checks each domain's homepage and root files, and puts the results next to each other: a **14-point scorecard**, a table of which **AI crawlers** each site allows, and every detail it collected.

- ✅ HTTPS, HTTP→HTTPS redirect, HSTS, redirect hops, compression, response time
- ✅ CMS / framework (WordPress, Shopify, Webflow, Next.js…) and CDN (Cloudflare, Fastly, Vercel…)
- ✅ Schema types, Organization schema, hreflang, canonical, mobile viewport, Open Graph, modern image formats
- ✅ robots.txt, XML sitemap, **llms.txt**, and rules for **10 AI crawlers** (GPTBot, ClaudeBot, PerplexityBot…)
- ✅ Optional Google PageSpeed Insights mobile scores

## 📊 Why this matters

> **Technical SEO Still Matters for AI Search** · NP Digital, November 2024 (409 SEO expert rankings)
> - Page speed and mobile-friendliness scored over 8.0.
> - Search intent match and structured data stayed above 7.5.
> - Factors like XML sitemaps and HTTPS still ranked meaningfully.
>
> **Structured Data Is Critical for GEO Performance** · NP Digital, October 2025
> - AI answers compete directly with both organic and paid visibility.
> - Structured data boosts inclusion in AI-driven results.
>
> Data: [technical SEO for AI search](https://neilpatel.com/marketing-stats/technical-seo-ai-search/) · [structured data and GEO](https://neilpatel.com/marketing-stats/structured-data-and-geo/)

**How competitor-tech-stack-audit uses this:** the scorecard checks the technical factors this data says still matter, HTTPS, mobile, speed, sitemaps and structured data, plus the AI-search signals you control yourself: llms.txt and which AI crawlers your robots.txt lets in.

<a id="quick-start"></a>

## 🚀 Quick start

```bash
git clone https://github.com/marketing-MEER/competitor-tech-stack-audit.git
cd competitor-tech-stack-audit
pip install -e .

# try it on two public practice sites
competitor-tech-stack-audit books.toscrape.com quotes.toscrape.com

# your site first, then competitors
competitor-tech-stack-audit yoursite.com rival-one.com rival-two.com --pagespeed --psi-key YOUR_KEY
```

This writes **`tech_stack_audit.html`** (a formatted report) and **`tech_stack_audit.xlsx`** (all data).

> [!NOTE]
> `--pagespeed` uses Google's free PageSpeed Insights API. Without a key, Google often refuses requests because the keyless quota is shared, and the report will say so. A free key takes 2 minutes: [Get an API key](https://developers.google.com/speed/docs/insights/v5/get-started#APIKey). Pass it with `--psi-key` or set `PSI_API_KEY`.

<a id="how-it-works"></a>

## ⚙️ How it works

For each domain (with a pause between domains):

1. Request `http://domain/` to see if it redirects to HTTPS, then load the homepage over HTTPS and time it.
2. Read the response headers: compression, HSTS, server, CDN fingerprints.
3. Parse the homepage HTML:
   - CMS / framework fingerprints, JSON-LD and microdata schema types, canonical, viewport
   - hreflang tags, Open Graph, script and image counts, WebP/AVIF images
4. Fetch `/robots.txt`: sitemap lines, and whether each AI crawler may fetch the homepage. No robots.txt means everything is allowed.
5. Look for `/sitemap.xml` when robots.txt lists none, and for `/llms.txt`.
6. Optionally call PageSpeed Insights (mobile): performance score, LCP, CLS and field INP.

**The 14-point scorecard:** Serves HTTPS · HTTP→HTTPS redirect · HSTS · Mobile viewport · XML sitemap · robots.txt · Canonical on homepage · Structured data · Organization schema · llms.txt · Open Graph · Compression · Homepage under 800 ms · At most 1 redirect.

### Options

| Option | Default | What it does |
|---|---|---|
| `--pagespeed` | off | Add PageSpeed Insights mobile scores |
| `--psi-key` | env `PSI_API_KEY` | Free PageSpeed API key |
| `--delay` | `1.0` | Seconds between domains |
| `-o`, `--output` | `tech_stack_audit` | Report name; writes `.html` and `.xlsx` |

<a id="report"></a>

## 📄 The report

| Section / Excel sheet | Shows |
|---|---|
| Score cards | Each domain's score out of 14 |
| **Scorecard** | ✅ / ❌ per check per domain (your site is the first column) |
| **AI crawlers** | allowed / blocked for GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended, CCBot, Applebot-Extended, Bytespider |
| **Details** | Every field collected: CMS, CDN, schema types, hreflang count, page weight, sitemap URL, PageSpeed results… |

<details>
<summary>📄 Example: real output for the two public practice sites</summary>

| check | books.toscrape.com | quotes.toscrape.com |
|---|---|---|
| Serves HTTPS | ✅ | ✅ |
| HTTP redirects to HTTPS | ❌ | ❌ |
| HSTS header | ✅ | ✅ |
| Mobile viewport | ✅ | ❌ |
| XML sitemap | ❌ | ❌ |
| Structured data | ❌ | ✅ |
| Homepage under 800 ms | ❌ | ✅ |
| … | | |
| **Score** | **4/14** | **5/14** |

Practice sites are built for scraping exercises, not SEO, so low scores are expected. Results on live sites change over time.

</details>

## 🧰 More free SEO tools

This repo is one tool in the **[SEO Toolbox](https://github.com/marketing-MEER/seo-toolbox)**, a family of free, single-purpose SEO tools. Related:
- **ai-crawler-access-checker**: a deeper look at AI crawler rules across many sites
- **robots-sitemap-validator**: validate robots.txt and every sitemap URL
- [seo-workhorse](https://github.com/marketing-MEER/seo-workhorse): audit, clustering, redirects and GSC quick wins in one CLI

<a id="faq"></a>

## ❓ FAQ

<details><summary><b>It only checks the homepage?</b></summary>

Yes, plus root files (robots.txt, sitemap, llms.txt). Site-wide setup like CMS, CDN, HTTPS and crawler rules shows on the homepage. For page-by-page issues, use a crawler such as [seo-workhorse](https://github.com/marketing-MEER/seo-workhorse) `audit`.
</details>

<details><summary><b>CMS shows "unknown / custom". Is that wrong?</b></summary>

Not always. Headless and custom builds often hide their stack, and some sites strip fingerprints on purpose. The detector only reports what it can see in the HTML.
</details>

<details><summary><b>Should I block AI crawlers?</b></summary>

It's a business decision. Blocking training crawlers (like CCBot or Google-Extended) is different from blocking search/answer crawlers (like OAI-SearchBot or PerplexityBot), which can cite and link to you. The table shows what each competitor chose.
</details>

<details><summary><b>Is my data sent anywhere?</b></summary>

Only to the domains you list, plus Google's PageSpeed API if you use `--pagespeed`. The report is written on your computer.
</details>

## 🧪 Tests

```bash
python -m unittest discover -s tests -t . -v
```

The tests run two small fake websites on a local server, so they need no internet.

## 📄 License

[MIT](LICENSE). Free for personal and commercial use. Benchmark figures © their original publishers, quoted with a link to the source.

<a id="author"></a>

## 👤 Author

**Meer Hamza** · SEO Team Lead · Berlin 🇩🇪
10+ years in SEO, AEO and GEO. I build small tools that take the spreadsheet work out of SEO.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/meerhamza-seo)
[![Email](https://img.shields.io/badge/Email-meerhamza5%40gmail.com-D14836?logo=gmail&logoColor=white)](mailto:meerhamza5@gmail.com)

<div align="center">

**If this saved you time, a ⭐ helps other SEOs find it.**

</div>
