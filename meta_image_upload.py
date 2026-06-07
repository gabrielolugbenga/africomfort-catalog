#!/usr/bin/env python3
import os, csv, time, requests, io, json

ACCESS_TOKEN  = os.getenv("META_ACCESS_TOKEN", "")
CATALOG_ID    = "838688529302207"
CSV_URL       = "https://gabrielolugbenga.github.io/africomfort-catalog/catalog.csv"
GRAPH_BASE    = "https://graph.facebook.com/v19.0"
REQUEST_DELAY = 0.3

def fetch_csv(url):
    print(f"📥 CSV : {url}")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(r.text)))
    print(f"   → {len(rows)} produits\n")
    return rows

def update_product(retailer_id, image_url, title):
    payload = {
        "access_token": ACCESS_TOKEN,
        "requests": [{
            "method": "UPDATE",
            "retailer_id": retailer_id,
            "data": {
                "image_url": image_url,
                "name": title,
            }
        }]
    }
    r = requests.post(f"{GRAPH_BASE}/{CATALOG_ID}/batch", json=payload, timeout=30)
    result = r.json()
    if isinstance(result, list) and result[0].get("success"):
        return True
    if "handles" in result:
        return True
    print(f"   ✗ {result}")
    return False

def main():
    print("\n══════════════════════════════════════")
    print("  AFRICOMFORT — Catalog Image Update")
    print("══════════════════════════════════════\n")
    products = fetch_csv(CSV_URL)
    ok, err, log = 0, 0, []
    for i, p in enumerate(products):
        rid   = p.get("id","").strip()
        img   = p.get("image_url","").strip()
        title = p.get("title", rid)
        if not rid or not img:
            continue
        print(f"[{i+1:3d}/{len(products)}] {rid} — {title[:40]}")
        if update_product(rid, img, title):
            print(f"        ✓ OK\n")
            ok += 1
            log.append({"id": rid, "status": "ok"})
        else:
            err += 1
            log.append({"id": rid, "status": "error"})
        time.sleep(REQUEST_DELAY)
    print("══════════════════════════════════════")
    print(f"  ✓ Succès : {ok} | ✗ Erreurs : {err}")
    with open("upload_results.json","w") as f:
        json.dump(log, f, indent=2)
    print("  Log → upload_results.json")

if __name__ == "__main__":
    main()
