#!/usr/bin/env python3
"""Scrape Amazon review data for all cameras using browser CDP connection."""
import json
import time
import websocket
import ssl

CDP_URL = "ws://127.0.0.1:18792/cdp"

# Camera search queries mapped to our ASIN
cameras = {
    "sony-fx3": {"asin": "B0F7RXXGH1", "query": "Sony FX3 cinema camera body"},
    "sony-fx6": {"asin": "B08LBGTZ1K", "query": "Sony FX6 cinema camera"},
    "sony-fx30": {"asin": "B0BG2BB77N", "query": "Sony FX30 cinema camera"},
    "sony-a7siii": {"asin": "B08HGMSYNY", "query": "Sony A7S III camera body"},
    "sony-a7cii": {"asin": "B0CHFKZXQF", "query": "Sony A7C II camera body"},
    "sony-a7iv": {"asin": "B09JZT6YK5", "query": "Sony A7 IV camera body"},
    "sony-zve10ii": {"asin": "B0D9NPF8QN", "query": "Sony ZV-E10 II camera"},
    "sony-a6700": {"asin": "B0C5SDNXQM", "query": "Sony A6700 camera body"},
    "canon-r5ii": {"asin": "B0DBBRT7G5", "query": "Canon EOS R5 Mark II camera"},
    "canon-r5c": {"asin": "B09RVJQXLV", "query": "Canon EOS R5 C camera"},
    "canon-r6iii": {"asin": "B0FZVVLR9D", "query": "Canon EOS R6 Mark III camera"},
    "canon-r7": {"asin": "B0B27NSHB5", "query": "Canon EOS R7 camera body"},
    "canon-r8": {"asin": "B0BVBKWG6C", "query": "Canon EOS R8 camera body"},
    "canon-r50": {"asin": "B0BVD3BPGX", "query": "Canon EOS R50 camera"},
    "canon-c70": {"asin": "B08KSFKG9L", "query": "Canon C70 cinema camera"},
    "canon-c80": {"asin": "B0DCX5XP2Y", "query": "Canon C80 cinema camera"},
    "panasonic-s5iix": {"asin": "B0BS1KRN8Y", "query": "Panasonic S5 IIX camera"},
    "panasonic-s5ii": {"asin": "B0BS1C53HB", "query": "Panasonic S5 II camera body"},
    "panasonic-gh7": {"asin": "B0D8BQXJLC", "query": "Panasonic GH7 camera"},
    "panasonic-gh6": {"asin": "B09SHDFWXY", "query": "Panasonic GH6 camera body"},
    "panasonic-g9ii": {"asin": "B0BS1NXFQP", "query": "Panasonic G9 II camera"},
    "blackmagic-pocket4k": {"asin": "B07C5MFN1Z", "query": "Blackmagic Pocket Cinema 4K"},
    "blackmagic-pocket6kg2": {"asin": "B09MFKYYXS", "query": "Blackmagic Pocket Cinema 6K G2"},
    "blackmagic-cc6k": {"asin": "B0CMXF12Z1", "query": "Blackmagic Cinema Camera 6K"},
    "blackmagic-pyxis": {"asin": "B0DC2XX9QN", "query": "Blackmagic PYXIS 6K camera"},
    "fujifilm-xh2s": {"asin": "B0B1VKPVW4", "query": "Fujifilm X-H2S camera body"},
    "fujifilm-xh2": {"asin": "B0BHRDTLXF", "query": "Fujifilm X-H2 camera body"},
    "fujifilm-xt5": {"asin": "B0BLP2NY6Q", "query": "Fujifilm X-T5 camera body"},
    "fujifilm-xs20": {"asin": "B0C5HZSXGL", "query": "Fujifilm X-S20 camera"},
    "nikon-z6iii": {"asin": "B0D64JJQHJ", "query": "Nikon Z6 III camera body"},
    "nikon-z8": {"asin": "B0C3GM1BXH", "query": "Nikon Z8 camera body"},
    "nikon-z50ii": {"asin": "B0DG8N4VRZ", "query": "Nikon Z50 II camera"},
    "dji-osmo-pocket3": {"asin": "B0CK19TPXH", "query": "DJI Osmo Pocket 3"},
    "gopro-hero13": {"asin": "B0DCFB1ZYT", "query": "GoPro Hero 13 Black"},
    "red-komodo": {"asin": "B096LHCCXM", "query": "RED Komodo 6K camera"},
}

msg_id = 0

def send_cdp(ws, method, params=None):
    global msg_id
    msg_id += 1
    msg = {"id": msg_id, "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp
        # skip events

def scrape_camera(ws, camera_id, info):
    query = info["query"].replace(" ", "+")
    target_asin = info["asin"]
    url = f"https://www.amazon.com/s?k={query}"
    
    # Navigate
    send_cdp(ws, "Page.navigate", {"url": url})
    time.sleep(4)  # Wait for page load
    
    # Extract review data using JS
    js = f"""
    (() => {{
        const targetAsin = "{target_asin}";
        // First try to find exact ASIN match
        const allItems = document.querySelectorAll('[data-asin]');
        let bestMatch = null;
        
        for (const el of allItems) {{
            const asin = el.getAttribute('data-asin');
            if (!asin) continue;
            
            const ratingBtn = el.querySelector('[aria-label*="out of 5 stars"]');
            const countLink = el.querySelector('a[href*="customerReviews"]');
            const priceWhole = el.querySelector('.a-price .a-price-whole');
            const priceFrac = el.querySelector('.a-price .a-price-fraction');
            const titleEl = el.querySelector('h2');
            
            if (!titleEl) continue;
            
            let rating = null;
            if (ratingBtn) {{
                const match = ratingBtn.getAttribute('aria-label').match(/([\d.]+) out of 5/);
                if (match) rating = parseFloat(match[1]);
            }}
            
            let reviewCount = null;
            if (countLink) {{
                const text = countLink.textContent.trim();
                const numMatch = text.replace(/,/g, '').match(/(\d+)/);
                if (numMatch) reviewCount = parseInt(numMatch[1]);
            }}
            
            let price = null;
            if (priceWhole) {{
                const whole = priceWhole.textContent.replace(/[,.\s]/g, '');
                const frac = priceFrac ? priceFrac.textContent : '00';
                price = parseFloat(whole + '.' + frac);
            }}
            
            const title = titleEl.textContent.trim().substring(0, 120);
            
            if (asin === targetAsin) {{
                return JSON.stringify({{
                    asin, title, rating, reviewCount, price, exact: true
                }});
            }}
            
            // Track first camera result as fallback
            if (!bestMatch && rating !== null) {{
                bestMatch = {{asin, title, rating, reviewCount, price, exact: false}};
            }}
        }}
        
        // Return best match if no exact ASIN found
        if (bestMatch) return JSON.stringify(bestMatch);
        return JSON.stringify(null);
    }})()
    """
    
    result = send_cdp(ws, "Runtime.evaluate", {"expression": js, "returnByValue": True})
    try:
        value = result.get("result", {}).get("result", {}).get("value")
        if value:
            data = json.loads(value)
            return data
    except:
        pass
    return None

def main():
    ws = websocket.create_connection(CDP_URL, sslopt={"cert_reqs": ssl.CERT_NONE})
    
    # Enable Page domain
    send_cdp(ws, "Page.enable")
    
    results = {}
    total = len(cameras)
    
    for i, (camera_id, info) in enumerate(cameras.items(), 1):
        print(f"[{i}/{total}] Scraping {camera_id}...", flush=True)
        try:
            data = scrape_camera(ws, camera_id, info)
            if data:
                results[camera_id] = data
                exact = "✓" if data.get("exact") else "~"
                print(f"  {exact} {data.get('rating')} stars, {data.get('reviewCount')} reviews, ${data.get('price')}")
            else:
                print(f"  ✗ No data found")
                results[camera_id] = {"asin": info["asin"], "rating": None, "reviewCount": None, "price": None, "exact": False}
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results[camera_id] = {"asin": info["asin"], "rating": None, "reviewCount": None, "price": None, "exact": False}
        
        # Rate limit - don't hammer Amazon
        time.sleep(2)
    
    # Save results
    with open("amazon-review-data.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDone! Saved {len(results)} results to amazon-review-data.json")
    
    # Summary
    found = sum(1 for r in results.values() if r.get("rating") is not None)
    exact = sum(1 for r in results.values() if r.get("exact"))
    print(f"Found ratings: {found}/{total}")
    print(f"Exact ASIN matches: {exact}/{total}")
    
    ws.close()

if __name__ == "__main__":
    main()
