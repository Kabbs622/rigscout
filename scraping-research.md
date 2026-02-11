# Scraping API Research — RigScout

## The Problem
We need to scrape product data (price, rating, review count, buy links) from:
- **Amazon** (35+ cameras, hardest target)
- **B&H** (done via Firecrawl)
- **Adorama** (done via listing page method)

Firecrawl is maxed out. Need alternatives that scale to hundreds of products.

---

## What Worked (Adorama)
**Category listing pages** — one fetch gives SKU, price, and review count for dozens of products. No bot detection, no rate limiting. This is the gold standard approach: find the retailer's listing/search pages and parse them instead of hitting individual product pages.

---

## Option 1: Amazon Associates Creators API (FREE, Official)
- **Amazon PA-API 5.0** is being deprecated **April 30, 2026**
- Replacement: **Creators API** (new Amazon affiliate API)
- **FREE** if you have an Amazon Associates account
- Returns: product title, price, rating, review count, images, buy links
- Rate limited but sufficient for our scale (35 cameras)
- **Affiliate links built in** — every link earns commission
- **Requirement**: Need an approved Amazon Associates account
- **Verdict**: ✅ BEST OPTION if Kyle has/gets Amazon Associates account. Free, legal, gives affiliate links too.

## Option 2: ScraperAPI ($0, 5K free credits)
- **Free tier**: 5,000 API calls, no credit card needed
- Handles Amazon anti-bot (rotating proxies, CAPTCHAs)
- Returns raw HTML — we'd parse it ourselves
- Amazon structured endpoint returns JSON with product data
- 35 cameras = 35 API calls = well within free tier
- **Paid**: starts at $49/mo for 100K credits
- **Verdict**: ✅ Good fallback. 5K free calls is way more than we need.

## Option 3: Scrapingdog ($0, 1K free credits)
- **Free tier**: 1,000 credits, no credit card
- Fastest tested (3.55s avg for Amazon)
- Dedicated Amazon Product endpoint → returns JSON
- $20/mo for 100K credits (cheapest paid)
- 35 cameras = 35 credits = well within free tier
- **Verdict**: ✅ Good option, fastest, 1K credits enough for our needs.

## Option 4: WebScrapingAPI ($0, 5K free/month)
- **Most generous free tier**: 5,000 requests/month ongoing
- General scraper (not Amazon-specific)
- May struggle with Amazon's anti-bot
- **Verdict**: 🟡 Good for Adorama/B&H backup, risky for Amazon.

## Option 5: Oxylabs (free trial, 2K results)
- Premium scraper, handles Amazon well
- Free trial: 2K results (enough for our 35 cameras)
- Paid: $1.25-$1.35 per 1K requests
- **Verdict**: 🟡 Overkill for our scale, but free trial covers it.

## Option 6: Our Own Method (Category Page Scraping)
- **What we did for Adorama**: fetch brand listing pages, parse review counts
- **For Amazon**: could search "Sony mirrorless camera" on Amazon and parse the search results page
- Search results show: title, price, rating, review count
- Uses `web_fetch` — no API key needed, no cost
- Risk: Amazon may block, but search pages are lighter protection
- **Verdict**: ✅ Try this first. Free, no API needed.

## Option 7: RapidAPI Amazon Endpoints
- Multiple Amazon scraper APIs on RapidAPI marketplace
- Many have free tiers (50-500 requests/month)
- Quality varies widely
- **Verdict**: 🟡 Hit or miss, worth checking specific providers.

---

## Recommendation (Priority Order)

### For Amazon:
1. **Try category/search page scraping first** (free, same method that worked on Adorama)
2. **If blocked → ScraperAPI free tier** (5K credits, no card needed)
3. **Long-term → Amazon Associates/Creators API** (free, official, gives affiliate revenue)

### For B&H refresh:
- Category listing pages (same Adorama method should work)

### For general scalability:
- The listing page approach scales to hundreds of cameras with minimal requests
- One page load = 20-50 products parsed
- No bot detection on listing/search pages
- This is the method to build the system around

---

## Amazon Associates Note
Kyle should sign up for Amazon Associates (affiliate program) if not already. Benefits:
- Free API access to product data (Creators API)
- Every buy link on RigScout earns commission
- This is the sustainable long-term play for monetization anyway
- Sign up: https://affiliate-program.amazon.com/

---

*Last updated: 2026-02-10*
