#!/usr/bin/env python3
"""Scrape Amazon product data using the Creators API for all RigScout cameras."""

import csv
import json
import time
import sys

from amazon_creatorsapi import AmazonCreatorsApi, Country

# Credentials
CREDENTIAL_ID = "uu4af44re6ao2pgdinkhagndu"
CREDENTIAL_SECRET = "vdm3mijoo99inajelhvh0khj3a2lcelr1pd39oq25g88b13qdlv"
VERSION = "2.1"
TAG = sys.argv[1] if len(sys.argv) > 1 else "rigscout-20"  # Pass affiliate tag as arg

# Load ASINs from master CSV
asins = {}
with open("rigscout-master-data.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        link = row.get("amazonLink", "")
        if "/dp/" in link:
            asin = link.split("/dp/")[1].split("/")[0].split("?")[0]
            asins[row["id"]] = asin

print(f"Found {len(asins)} cameras with ASINs")

# Init API
api = AmazonCreatorsApi(
    credential_id=CREDENTIAL_ID,
    credential_secret=CREDENTIAL_SECRET,
    version=VERSION,
    tag=TAG,
    country=Country.US,
    throttling=1,
)

# Batch in groups of 10 (API limit)
asin_list = list(asins.items())
results = {}

for i in range(0, len(asin_list), 10):
    batch = asin_list[i : i + 10]
    batch_asins = [asin for _, asin in batch]
    batch_ids = {asin: cam_id for cam_id, asin in batch}

    print(f"\nFetching batch {i // 10 + 1}: {[cam_id for cam_id, _ in batch]}")

    try:
        items = api.get_items(batch_asins)
        for item in items:
            asin = item.asin
            cam_id = batch_ids.get(asin, asin)

            # Extract data
            data = {
                "asin": asin,
                "title": None,
                "price": None,
                "list_price": None,
                "rating": None,
                "review_count": None,
                "affiliate_url": None,
                "image_url": None,
            }

            if item.item_info and item.item_info.title:
                data["title"] = item.item_info.title.display_value

            if item.offers_v2 and item.offers_v2.listings:
                listing = item.offers_v2.listings[0]
                if listing.price and listing.price.money:
                    data["price"] = listing.price.money.amount
                if listing.saving_basis and listing.saving_basis.money:
                    data["list_price"] = listing.saving_basis.money.amount

            # Detail page URL (affiliate link)
            if item.detail_page_url:
                data["affiliate_url"] = item.detail_page_url

            # Images
            if item.images and item.images.primary and item.images.primary.large:
                data["image_url"] = item.images.primary.large.url

            # Customer reviews
            if item.customer_reviews:
                cr = item.customer_reviews
                if hasattr(cr, 'star_rating') and cr.star_rating:
                    data["rating"] = cr.star_rating.value
                if hasattr(cr, 'count') and cr.count:
                    data["review_count"] = cr.count

            results[cam_id] = data
            print(f"  ✓ {cam_id}: ${data['price']} | {data['rating']}★ ({data['review_count']} reviews)")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        # Try individual items on batch failure
        for cam_id, asin in batch:
            try:
                time.sleep(1)
                items = api.get_items([asin])
                if items:
                    item = items[0]
                    data = {
                        "asin": asin,
                        "title": item.item_info.title.display_value if item.item_info and item.item_info.title else None,
                        "price": None,
                        "list_price": None,
                        "rating": None,
                        "review_count": None,
                        "affiliate_url": item.detail_page_url,
                        "image_url": None,
                    }
                    if item.offers_v2 and item.offers_v2.listings:
                        listing = item.offers_v2.listings[0]
                        if listing.price and listing.price.money:
                            data["price"] = listing.price.money.amount
                    if item.customer_reviews:
                        cr = item.customer_reviews
                        if hasattr(cr, 'star_rating') and cr.star_rating:
                            data["rating"] = cr.star_rating.value
                        if hasattr(cr, 'count') and cr.count:
                            data["review_count"] = cr.count
                    results[cam_id] = data
                    print(f"  ✓ {cam_id} (individual): ${data['price']}")
            except Exception as e2:
                print(f"  ✗ {cam_id}: {e2}")

# Save results
with open("amazon-data.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved {len(results)} cameras to amazon-data.json")
