{
    "name": "POS Administration Fee",
    "summary": "Auto-add a configurable administration fee to small POS orders",
    "version": "17.0.1.0.0",
    "category": "Sales/Point of Sale",
    "author": "Miguel Vanduffel",
    "maintainer": "Miguel Vanduffel",
    "company": "Arplama",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_administration_fee/static/src/js/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
