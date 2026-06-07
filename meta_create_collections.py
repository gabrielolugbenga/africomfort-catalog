#!/usr/bin/env python3
import os, csv, io, json, requests

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
CATALOG_ID   = "838688529302207"
GRAPH_BASE   = "https://graph.facebook.com/v19.0"
CSV_URL      = "https://gabrielolugbenga.github.io/africomfort-catalog/catalog.csv"

PREFIXES = {
    "BOI-":   "Boissons",
    "FAR-":   "Farines et Feculents",
    "DEJ-":   "Petit Dejeuner",
    "HUI-":   "Huiles",
    "VEG-":   "Legumes et Feuilles",
    "SEAS-":  "Epices et Assaisonnements",
    "VIPO-":  "Viandes et Poissons",
    "GOU-":   "Goutters et Snacks",
    "COS-":   "Cosmetiques",
    "RINOU-": "Riz et Nouilles",
}

def fetch_ids_by_category():
    r = requests.get(CSV_URL, timeout=15)
    r.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(r.text)))
    groups = {prefix: [] for prefix in PREFIXES}
    for row in rows:
        rid = row.get("id", "").strip()
        for prefix in PREFIXES:
            if rid.startswith(prefix):
                groups[prefix].append(rid)
                break
    return groups

def list_existing():
    r = requests.get(f"{GRAPH_BASE}/{CATALOG_ID}/product_sets",
        params={"access_token": ACCESS_TOKEN, "fields": "id,name"}, timeout=30)
    return {c["name"]: c["id"] for c in r.json().get("data", [])}

def create_collection(name, retailer_ids):
    filter_obj = {"retailer_id": {"is_any": retailer_ids}}
    r = requests.post(
        f"{GRAPH_BASE}/{CATALOG_ID}/product_sets",
        data={"access_token": ACCESS_TOKEN, "name": name,
              "filter": json.dumps(filter_obj)},
        timeout=30)
    result = r.json()
    if "id" in result:
        return result
    print(f"   ✗ {result}")
    return None

def main():
    print("\n══════════════════════════════════════════")
    print("  AFRICOMFORT — Creation des Collections")
    print("══════════════════════════════════════════\n")

    groups   = fetch_ids_by_category()
    existing = list_existing()
    print(f"Existantes : {list(existing.keys())}\n")

    ok, skip, err = 0, 0, 0
    for prefix, name in PREFIXES.items():
        ids = groups.get(prefix, [])
        if not ids:
            print(f"  ⚠ '{name}' — aucun produit trouvé, ignoré")
            skip += 1
            continue
        if name in existing:
            print(f"  ⏭ '{name}' existe déjà ({len(ids)} produits)")
            skip += 1
            continue
        print(f"  + '{name}' ({len(ids)} produits) ...")
        result = create_collection(name, ids)
        if result:
            print(f"    ✓ ID: {result['id']}"); ok += 1
        else:
            err += 1

    print(f"\n  ✓ Créées : {ok} | ⏭ Ignorées : {skip} | ✗ Erreurs : {err}\n")

if __name__ == "__main__":
    main()
