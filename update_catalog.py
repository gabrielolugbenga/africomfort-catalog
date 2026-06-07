#!/usr/bin/env python3
import os, csv, io, json, time, requests, subprocess
from pathlib import Path

RAILWAY_URL  = "https://web-production-9581a.up.railway.app"
META_TOKEN   = os.getenv("META_ACCESS_TOKEN", "")
CATALOG_ID   = "838688529302207"
GRAPH_BASE   = "https://graph.facebook.com/v19.0"
IMAGES_DIR   = Path("images")
IMAGES_DIR.mkdir(exist_ok=True)

def step(msg): print(f"\n{'='*50}\n  {msg}\n{'='*50}")

step("1. Downloading CSV from Railway")
r = requests.get(f"{RAILWAY_URL}/catalog-feed", timeout=30)
r.raise_for_status()
with open("catalog.csv", "w") as f:
    f.write(r.text)
products = list(csv.DictReader(io.StringIO(r.text)))
print(f"  -> {len(products)} products")

step("2. Downloading missing images")
new_images = 0
for p in products:
    pid = p.get("id", "").strip()
    img_url = p.get("image_url", "")
    if "/product-image/" not in img_url:
        continue
    odoo_id = img_url.split("/product-image/")[1].split("?")[0]
    img_path = IMAGES_DIR / f"{pid}.jpg"
    if img_path.exists():
        continue
    try:
        r_img = requests.get(f"{RAILWAY_URL}/product-image/{odoo_id}", timeout=15)
        if r_img.status_code == 200:
            img_path.write_bytes(r_img.content)
            new_images += 1
            print(f"  + {pid}.jpg")
    except Exception as e:
        print(f"  x {pid} - {e}")
print(f"  -> {new_images} new images")

step("3. Updating Meta catalog")
ok, err = 0, 0
for i, p in enumerate(products):
    rid   = p.get("id", "").strip()
    price = p.get("price", "0").strip()
    img   = p.get("image_url", "").strip()
    title = p.get("title", "").strip()
    if not rid or not META_TOKEN:
        continue
    payload = {
        "access_token": META_TOKEN,
        "requests": [{
            "method": "UPDATE",
            "retailer_id": rid,
            "data": {
                "name":     title,
                "price":    str(int(float(price) * 100)),
                "currency": "EUR",
                "image_url": img,
            }
        }]
    }
    resp = requests.post(f"{GRAPH_BASE}/{CATALOG_ID}/batch", json=payload, timeout=30)
    result = resp.json()
    if isinstance(result, list) and result[0].get("success"):
        ok += 1
    elif "handles" in result:
        ok += 1
    else:
        print(f"  x {rid}: {result}")
        err += 1
    if i % 30 == 0:
        print(f"  [{i+1}/{len(products)}]")
    time.sleep(0.3)

print(f"\n  OK: {ok} | Errors: {err}")
step("Done")
