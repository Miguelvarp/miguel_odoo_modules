{
    "name": "Arplama — Product Label A5 (2x4)",
    "version": "19.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "A5 product labels, 8 per page (2 columns x 4 rows)",
    "description": """
Adds a "2 x 4 (A5)" option to the product Print Labels wizard (Settings-free,
it appears in the same Format dropdown as Dymo / 2x7 / 4x7 / 4x12).

Each label shows the product name, internal reference and barcode.
8 labels fit on one A5 page (148 x 210 mm); more products flow onto new pages.
    """,
    "author": "Arplama",
    "depends": ["product"],
    "data": [
        "views/product_label_templates.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
