import requests
import xmlrpc.client
import ssl
from PIL import Image
import io
import os
import urllib3

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

ODOO_URL = "https://africomfort-foods.odoo.com"
ODOO_DB = "africomfort-foods"
ODOO_USER = "africomfortfoods@gmail.com"
ODOO_PASSWORD = "2b3ac911f7cb7142669d208c2b80b0900f666015"

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.template', 'search_read',
    [[['sale_ok', '=', True], ['active', '=', True], ['is_published', '=', True]]],
    {'fields': ['name', 'default_code', 'list_price', 'categ_id', 'description_sale'], 'limit': 200}
)

os.makedirs("images", exist_ok=True)
session = requests.Session()
session.verify = False

catalog_lines = ["id,title,description,price,currency,image_url,brand,condition,availability,google_product_category,link"]

for p in products:
    product_id = p['id']
    retailer_id = p.get('default_code') or str(product_id)
    
    img_url = f"{ODOO_URL}/web/image/product.template/{product_id}/image_1920"
    r = session.get(img_url, timeout=15)
    
    image_filename = f"images/{retailer_id}.jpg"
    if r.status_code == 200:
        try:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            w, h = img.size
            size = min(w, h)
            img = img.crop(((w-size)//2, (h-size)//2, (w+size)//2, (h+size)//2))
            img = img.resize((800, 800), Image.LANCZOS)
            img.save(image_filename, format="JPEG", quality=85)
            print(f"✅ {p['name']}")
        except Exception as e:
            print(f"❌ {p['name']}: {e}")
            image_filename = None
    else:
        print(f"⚠️ No image: {p['name']}")
        image_filename = None

    title = p.get('name', '')
    description = p.get('description_sale') or title
    price = f"{float(p.get('list_price', 0)):.2f}"
    category = (p.get('categ_id') or [0, 'General'])[1]
    image_url = f"https://gabrielolugbenga.github.io/africomfort-catalog/images/{retailer_id}.jpg" if image_filename else ""
    link = f"{ODOO_URL}/shop/product/{product_id}"
    
    catalog_lines.append(f'{retailer_id},"{title}","{description}",{price},EUR,{image_url},Africomfort Foods,new,in stock,"{category}",{link}')

with open("catalog.csv", "w") as f:
    f.write("\n".join(catalog_lines))

print(f"\nDone! {len(products)} products processed.")
