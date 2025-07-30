# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Pricelist Access",
    "summary": "Restrict access to product pricelists by user or group",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "Sygel,Odoo Community Association (OCA)",
    "website": "https://github.com/sygel-technology/sy-product-attribute",
    "depends": [
        "product",
    ],
    "data": [
        "security/security.xml",
        "views/product_pricelist_views.xml",
    ],
}
