"""
Suppliers, products, VAT rates.

B2C OSS rule (EU, since Jul 2021): the VAT rate of the DESTINATION country applies.
Suppliers must charge and remit the buyer's country VAT rate.

Two-tier party model
────────────────────
The simulation models cross-border B2C as follows:
  - SUPPLIERS         = EU-based **resellers** that import goods and sell
                        them to EU consumers. They are the DeemedImporter
                        on the customs message (and the seller_* columns
                        in the DB).
  - PRODUCERS         = non-EU **manufacturers** the supplier sources
                        from. They appear as the Seller block on each
                        SalesLineItem (the producer who actually made
                        the goods).
A given supplier may resell goods from multiple producers across the
same product category. The seeder picks one producer per transaction.
"""

COUNTRIES = ["FR", "DE", "ES", "IT", "NL", "PL", "IE"]

COUNTRY_NAMES = {
    "FR": "France",
    "DE": "Germany",
    "ES": "Spain",
    "IT": "Italy",
    "NL": "Netherlands",
    "PL": "Poland",
    "IE": "Ireland",
}

# Correct VAT rates per destination country and product category
VAT_RATES: dict[str, dict[str, float]] = {
    "FR": {
        "electronics":      0.20,
        "clothing":         0.20,
        "food":             0.055,
        "books":            0.055,
        "health":           0.10,
        "home_goods":       0.20,
        "cosmetics":        0.20,
        "sports":           0.20,
        "auto_accessories": 0.20,
    },
    "DE": {
        "electronics":      0.19,
        "clothing":         0.19,
        "food":             0.07,
        "books":            0.07,
        "health":           0.19,
        "home_goods":       0.19,
        "cosmetics":        0.19,
        "sports":           0.19,
        "auto_accessories": 0.19,
    },
    "ES": {
        "electronics":      0.21,
        "clothing":         0.21,
        "food":             0.10,
        "books":            0.04,
        "health":           0.10,
        "home_goods":       0.21,
        "cosmetics":        0.21,
        "sports":           0.21,
        "auto_accessories": 0.21,
    },
    "IT": {
        "electronics":      0.22,
        "clothing":         0.22,
        "food":             0.10,
        "books":            0.04,
        "health":           0.10,
        "home_goods":       0.22,
        "cosmetics":        0.22,
        "sports":           0.22,
        "auto_accessories": 0.22,
    },
    "NL": {
        "electronics":      0.21,
        "clothing":         0.21,
        "food":             0.09,
        "books":            0.09,
        "health":           0.21,
        "home_goods":       0.21,
        "cosmetics":        0.21,
        "sports":           0.21,
        "auto_accessories": 0.21,
    },
    "PL": {
        "electronics":      0.23,
        "clothing":         0.23,
        "food":             0.08,
        "books":            0.05,
        "health":           0.08,
        "home_goods":       0.23,
        "cosmetics":        0.23,
        "sports":           0.23,
        "auto_accessories": 0.23,
    },
    "IE": {
        "electronics":      0.23,
        "clothing":         0.23,
        "food":             0.00,   # zero-rated in Ireland
        "books":            0.00,   # zero-rated in Ireland
        "health":           0.00,   # zero-rated in Ireland
        "home_goods":       0.23,
        "cosmetics":        0.23,
        "sports":           0.23,
        "auto_accessories": 0.23,
    },
}

# Wrong-rate pool: rates a supplier might mistakenly apply
# (their own country's rates instead of the destination country's)
WRONG_RATE_POOL: dict[str, dict[str, float]] = VAT_RATES  # same structure, different country key


SUPPLIERS: list[dict] = [
    {
        "id": "SUP001",
        "name": "TechZone GmbH",
        "country": "DE",
        "vat_number": "DE123456789",
        "categories": ["electronics", "auto_accessories"],
        "products": [
            ("Wireless Headphones Pro",       "electronics",      149.99),
            ("4K Webcam Ultra",               "electronics",       89.99),
            ("USB-C Hub 7-in-1",              "electronics",       49.99),
            ("Mechanical Keyboard RGB",       "electronics",      129.99),
            ("Smart Home Speaker",            "electronics",      199.99),
            ("Portable Charger 20000mAh",     "electronics",       39.99),
            ("Car Dash Camera 4K",            "auto_accessories",  79.99),
            ("OBD2 Scanner Bluetooth",        "auto_accessories",  59.99),
            ("Car Phone Mount Wireless",      "auto_accessories",  29.99),
        ],
    },
    {
        "id": "SUP002",
        "name": "FashionHub Paris",
        "country": "FR",
        "vat_number": "FR98765432100",
        "categories": ["clothing"],
        "products": [
            ("Premium Wool Coat",             "clothing", 249.99),
            ("Designer Silk Scarf",           "clothing",  89.99),
            ("Leather Handbag Classic",       "clothing", 199.99),
            ("Cashmere Sweater",              "clothing", 149.99),
            ("Linen Summer Dress",            "clothing",  79.99),
            ("Slim-Fit Chinos",               "clothing",  69.99),
            ("Evening Gown Velvet",           "clothing", 299.99),
            ("Sports Jacket Waterproof",      "clothing", 119.99),
        ],
    },
    {
        "id": "SUP003",
        "name": "BioNatura S.L.",
        "country": "ES",
        "vat_number": "ESB12345678",
        "categories": ["food", "health"],
        "products": [
            ("Organic Extra Virgin Olive Oil 5L", "food",    29.99),
            ("Premium Iberian Ham 500g",           "food",    49.99),
            ("Saffron Threads 10g",                "food",    19.99),
            ("Manchego Cheese Aged 1kg",           "food",    24.99),
            ("Organic Almond Butter 350g",         "food",    14.99),
            ("Vitamin D3 + K2 Supplement",         "health",  24.99),
            ("Collagen Peptides Powder 500g",       "health",  39.99),
            ("Ashwagandha Capsules 90ct",           "health",  29.99),
            ("Organic Spirulina 250g",              "health",  19.99),
        ],
    },
    {
        "id": "SUP004",
        "name": "CasaDecor Milano",
        "country": "IT",
        "vat_number": "IT12345678901",
        "categories": ["home_goods"],
        "products": [
            ("Marble Serving Board Set",         "home_goods", 59.99),
            ("Linen Tablecloth 200x140cm",        "home_goods", 44.99),
            ("Handcrafted Ceramic Vase",          "home_goods", 34.99),
            ("Velvet Cushion Cover Set 4pc",      "home_goods", 49.99),
            ("Bamboo Bathroom Set 6pc",           "home_goods", 39.99),
            ("Scented Soy Candle Set 3pc",        "home_goods", 29.99),
            ("Copper Cookware Set 5pc",           "home_goods", 199.99),
            ("Murano Glass Pendant Light",        "home_goods", 149.99),
            ("Merino Wool Blanket",               "home_goods",  89.99),
        ],
    },
    {
        "id": "SUP005",
        "name": "SportsPro Amsterdam",
        "country": "NL",
        "vat_number": "NL123456789B01",
        "categories": ["sports"],
        "products": [
            ("Cycling Helmet MIPS Pro",          "sports", 119.99),
            ("Running Shoes Carbon Plate",       "sports", 189.99),
            ("Yoga Mat Premium 6mm",             "sports",  49.99),
            ("Resistance Bands Set 5pc",         "sports",  29.99),
            ("Foam Roller Deep Tissue",          "sports",  34.99),
            ("GPS Sports Watch",                 "sports", 299.99),
            ("Swimming Goggles Pro UV",          "sports",  24.99),
            ("Tennis Racket All-Carbon",         "sports", 149.99),
            ("Football Training Cones 20pc",     "sports",  19.99),
        ],
    },
    {
        "id": "SUP006",
        "name": "EcoBooks Warsaw",
        "country": "PL",
        "vat_number": "PL1234567890",
        "categories": ["books"],
        "products": [
            ("European History 1900-2000",           "books", 24.99),
            ("Mindfulness & Meditation Guide",       "books", 18.99),
            ("Atlas of Natural Sciences",            "books", 34.99),
            ("Children Encyclopedia Set 5vol",       "books", 89.99),
            ("Cooking Masterclass Collection 3vol",  "books", 59.99),
            ("Climate Change & Solutions",           "books", 21.99),
            ("Art of Photography Complete Guide",    "books", 44.99),
            ("Learning Python Programming",          "books", 39.99),
        ],
    },
    {
        "id": "SUP007",
        "name": "GourmetShop Lyon",
        "country": "FR",
        "vat_number": "FR12345678901",
        "categories": ["food"],
        "products": [
            ("Burgundy Pinot Noir 2019 6bt",     "food", 89.99),
            ("Artisan Camembert de Normandie",   "food", 12.99),
            ("Black Truffle Oil 100ml",          "food", 24.99),
            ("Foie Gras Terrine 180g",           "food", 34.99),
            ("Dijon Mustard Artisan 3-pack",     "food", 19.99),
            ("Herbes de Provence 100g",          "food",  9.99),
            ("Praline Chocolate Box 500g",       "food", 29.99),
            ("Champagne Brut NV 75cl",           "food", 49.99),
        ],
    },
    {
        "id": "SUP008",
        "name": "AutoParts Berlin",
        "country": "DE",
        "vat_number": "DE987654321",
        "categories": ["auto_accessories"],
        "products": [
            ("LED Headlight Kit H7",             "auto_accessories", 89.99),
            ("Car Air Freshener Set 10pc",       "auto_accessories", 14.99),
            ("Tire Pressure Gauge Digital",      "auto_accessories", 24.99),
            ("Seat Cover Set Universal",         "auto_accessories", 49.99),
            ("Cargo Net Trunk Organizer",        "auto_accessories", 19.99),
            ("Jump Starter 2000A Lithium",       "auto_accessories", 119.99),
            ("Roof Rack Crossbars",              "auto_accessories", 149.99),
            ("Car Polishing Kit Professional",   "auto_accessories",  59.99),
        ],
    },
    {
        "id": "SUP009",
        "name": "BeautyLine Rome",
        "country": "IT",
        "vat_number": "IT98765432109",
        "categories": ["cosmetics"],
        "products": [
            ("Rose & Hyaluronic Serum 30ml",         "cosmetics", 44.99),
            ("Retinol Night Cream 50ml",              "cosmetics", 54.99),
            ("Natural Mineral Sunscreen SPF50 100ml", "cosmetics", 24.99),
            ("Argan Oil Hair Treatment 100ml",        "cosmetics", 34.99),
            ("Vitamin C Brightening Mask 5pc",        "cosmetics", 29.99),
            ("Bamboo Charcoal Face Wash 150ml",       "cosmetics", 19.99),
            ("Luxury Perfume Eau de Parfum 50ml",     "cosmetics", 79.99),
            ("Shea Body Butter 250ml",                "cosmetics", 22.99),
        ],
    },
    {
        "id": "SUP010",
        "name": "TechAccessories Rotterdam",
        "country": "NL",
        "vat_number": "NL987654321B01",
        "categories": ["electronics"],
        "products": [
            ("Wireless Mouse Ergonomic",             "electronics", 39.99),
            ("Monitor Stand Dual Arm",               "electronics", 79.99),
            ("Cable Management Kit 50pc",            "electronics", 24.99),
            ("HDMI Switch 4-Port 4K",                "electronics", 34.99),
            ("Desk Pad Large 90x40cm",               "electronics", 29.99),
            ("Laptop Stand Adjustable Aluminium",    "electronics", 49.99),
            ("Smart Plug WiFi 4-Pack",               "electronics", 44.99),
            ("LED Desk Lamp USB-C",                  "electronics", 54.99),
        ],
    },
]


# ── Producers (non-EU manufacturers) ─────────────────────────────────────────
# Each producer is a real-world-plausible factory in a non-EU country. The
# `categories` list controls which item categories the producer can supply;
# the seeder uses pick_producer_for_category() to find a producer that
# matches the category of each transaction.
PRODUCERS: list[dict] = [
    # ── Electronics / accessories (China, Korea, Japan, Taiwan, Vietnam) ──
    {"id": "PROD-CN-001", "name": "ShenZhen TechFactory Co.",
     "country": "CN", "city": "Shenzhen",
     "categories": ["electronics", "auto_accessories"]},
    {"id": "PROD-CN-002", "name": "Guangzhou Electronics Mfg.",
     "country": "CN", "city": "Guangzhou",
     "categories": ["electronics"]},
    {"id": "PROD-KR-001", "name": "Seoul Display Industries",
     "country": "KR", "city": "Seoul",
     "categories": ["electronics", "cosmetics"]},
    {"id": "PROD-JP-001", "name": "Osaka Precision Components",
     "country": "JP", "city": "Osaka",
     "categories": ["electronics", "auto_accessories"]},
    {"id": "PROD-VN-001", "name": "Hanoi Electronics Assembly",
     "country": "VN", "city": "Hanoi",
     "categories": ["electronics"]},
    # ── Clothing (Vietnam, Bangladesh, India, Turkey) ─────────────────────
    {"id": "PROD-VN-002", "name": "Saigon Garment Co.",
     "country": "VN", "city": "Ho Chi Minh City",
     "categories": ["clothing"]},
    {"id": "PROD-BD-001", "name": "Dhaka Apparel Manufacturers",
     "country": "BD", "city": "Dhaka",
     "categories": ["clothing"]},
    {"id": "PROD-IN-001", "name": "Mumbai TextileWorks Pvt. Ltd.",
     "country": "IN", "city": "Mumbai",
     "categories": ["clothing", "home_goods"]},
    {"id": "PROD-TR-001", "name": "Istanbul Fashion Production",
     "country": "TR", "city": "Istanbul",
     "categories": ["clothing"]},
    # ── Food / health (Thailand, Brazil, Morocco) ──────────────────────────
    {"id": "PROD-TH-001", "name": "Bangkok Foods International",
     "country": "TH", "city": "Bangkok",
     "categories": ["food", "health"]},
    {"id": "PROD-BR-001", "name": "Sao Paulo Agricultural Co.",
     "country": "BR", "city": "Sao Paulo",
     "categories": ["food"]},
    {"id": "PROD-MA-001", "name": "Casablanca Natural Products",
     "country": "MA", "city": "Casablanca",
     "categories": ["food", "cosmetics", "health"]},
    # ── Cosmetics / beauty (Korea, China) ──────────────────────────────────
    {"id": "PROD-KR-002", "name": "Seoul BeautyTech Manufacturing",
     "country": "KR", "city": "Seoul",
     "categories": ["cosmetics"]},
    {"id": "PROD-CN-003", "name": "Shanghai Cosmetics Industries",
     "country": "CN", "city": "Shanghai",
     "categories": ["cosmetics"]},
    # ── Books / publishing (China, India, US) ─────────────────────────────
    {"id": "PROD-CN-004", "name": "Beijing Print House",
     "country": "CN", "city": "Beijing",
     "categories": ["books"]},
    {"id": "PROD-IN-002", "name": "Delhi Publishing Co.",
     "country": "IN", "city": "Delhi",
     "categories": ["books"]},
    {"id": "PROD-US-001", "name": "Chicago Print Group",
     "country": "US", "city": "Chicago",
     "categories": ["books"]},
    # ── Sports (China, Vietnam, Pakistan) ──────────────────────────────────
    {"id": "PROD-CN-005", "name": "Quanzhou Sports Equipment Co.",
     "country": "CN", "city": "Quanzhou",
     "categories": ["sports"]},
    {"id": "PROD-VN-003", "name": "Da Nang Athletic Wear",
     "country": "VN", "city": "Da Nang",
     "categories": ["sports", "clothing"]},
    {"id": "PROD-PK-001", "name": "Sialkot Sports Manufacturing",
     "country": "PK", "city": "Sialkot",
     "categories": ["sports"]},
    # ── Home goods (China, India, Vietnam) ─────────────────────────────────
    {"id": "PROD-CN-006", "name": "Foshan Home Furnishings",
     "country": "CN", "city": "Foshan",
     "categories": ["home_goods"]},
    {"id": "PROD-CN-007", "name": "Yiwu Household Goods",
     "country": "CN", "city": "Yiwu",
     "categories": ["home_goods"]},
    # ── Auto / accessories (China, Malaysia, Thailand) ─────────────────────
    {"id": "PROD-CN-008", "name": "Wenzhou Auto Parts Mfg.",
     "country": "CN", "city": "Wenzhou",
     "categories": ["auto_accessories"]},
    {"id": "PROD-MY-001", "name": "Penang Component Industries",
     "country": "MY", "city": "Penang",
     "categories": ["auto_accessories", "electronics"]},
    # ── Hong Kong wildcard — covers anything via consolidated trading ─────
    {"id": "PROD-HK-001", "name": "Hong Kong Trading & Mfg.",
     "country": "HK", "city": "Hong Kong",
     "categories": ["electronics", "clothing", "home_goods", "cosmetics", "auto_accessories", "sports"]},
]


def producers_for_category(category: str) -> list[dict]:
    """Return every producer that lists *category* in its categories list."""
    return [p for p in PRODUCERS if category in p["categories"]]


def producer_countries() -> set[str]:
    """ISO codes of every country where at least one producer is based.
    Useful for sanity checks (none should be inside the EU)."""
    return {p["country"] for p in PRODUCERS}
