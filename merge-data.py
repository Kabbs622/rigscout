#!/usr/bin/env python3
"""Merge Adorama + Amazon data into index.html camera database."""
import json, re, sys

# Load source data
with open('adorama-data.json') as f:
    adorama_list = json.load(f)
adorama = {a['id']: a for a in adorama_list}

with open('amazon-review-data.json') as f:
    amazon_reviews = json.load(f)

with open('amazon-affiliate-links.json') as f:
    amazon_links = json.load(f)

# ASIN corrections
asin_fixes = {
    'sony-fx6': 'B08NSHMG8X',
    'sony-fx30': 'B0BGQGBW8J',
}

# Read index.html
with open('index.html', 'r') as f:
    html = f.read()

# Find the cameras JSON array in the DB
# It starts with "cameras:[" and ends with "]"
db_match = re.search(r'const DB = \{\s*cameras:\s*\[(.+?)\],\s*lenses:', html, re.DOTALL)
if not db_match:
    print("ERROR: Could not find camera database in index.html")
    sys.exit(1)

cameras_str = db_match.group(1)

# Parse individual camera objects
# Each camera is a JSON object {...}
camera_objects = []
depth = 0
start = None
for i, ch in enumerate(cameras_str):
    if ch == '{' and depth == 0:
        start = i
    if ch == '{': depth += 1
    if ch == '}': depth -= 1
    if ch == '}' and depth == 0 and start is not None:
        camera_objects.append((start, i+1, cameras_str[start:i+1]))
        start = None

print(f"Found {len(camera_objects)} cameras in index.html")

updated_cameras_str = cameras_str
offset = 0

for start_pos, end_pos, cam_str in camera_objects:
    try:
        cam = json.loads(cam_str)
    except:
        print(f"  WARN: Could not parse camera at position {start_pos}")
        continue
    
    cam_id = cam.get('id', '')
    changed = False
    
    # Remove test salePrice if present
    if 'salePrice' in cam:
        del cam['salePrice']
        changed = True
    
    # Update Amazon link with affiliate tag + fix ASINs
    if cam_id in amazon_links:
        link_data = amazon_links[cam_id]
        asin = asin_fixes.get(cam_id, link_data['asin'])
        new_url = f"https://www.amazon.com/dp/{asin}?tag=c41cinema-20"
        if cam.get('amazonLink') != new_url:
            cam['amazonLink'] = new_url
            changed = True
    
    # Update Adorama link if we have a better one
    if cam_id in adorama:
        ad = adorama[cam_id]
        if ad.get('adorama_link') and cam.get('adoramaLink') != ad['adorama_link']:
            cam['adoramaLink'] = ad['adorama_link']
            changed = True
    
    # Add review data fields
    # Amazon
    if cam_id in amazon_reviews:
        ar = amazon_reviews[cam_id]
        if ar.get('rating') is not None:
            cam['amazonRating'] = ar['rating']
            cam['amazonReviews'] = ar['reviewCount']
            changed = True
    
    # Adorama
    if cam_id in adorama:
        ad = adorama[cam_id]
        rating = ad.get('adorama_rating', '')
        reviews = ad.get('adorama_review_count', '0')
        if rating and rating != '':
            cam['adoramaRating'] = float(rating)
            changed = True
        if reviews and int(reviews) > 0:
            cam['adoramaReviews'] = int(reviews)
            changed = True
    
    if changed:
        # Re-serialize - compact JSON
        new_cam_str = json.dumps(cam, separators=(',', ':'), ensure_ascii=False)
        adj_start = start_pos + offset
        adj_end = end_pos + offset
        updated_cameras_str = updated_cameras_str[:adj_start] + new_cam_str + updated_cameras_str[adj_end:]
        offset += len(new_cam_str) - (end_pos - start_pos)
        print(f"  Updated: {cam_id}")

# Replace in HTML
old_section = db_match.group(0)
new_section = old_section.replace(cameras_str, updated_cameras_str)
html = html.replace(old_section, new_section)

with open('index.html', 'w') as f:
    f.write(html)

print("\nDone! index.html updated.")
