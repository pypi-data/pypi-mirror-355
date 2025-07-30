# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    access_user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Access Users",
        help="Users in this field who belong to the 'Restrict "
        "Product Pricelist' group will have access to this "
        "pricelist. Leave this field empty if all users with "
        "general access to product pricelists model need access "
        "to this pricelist.",
    )
    access_group_ids = fields.Many2many(
        comodel_name="res.groups",
        string="Access Groups",
        help="Users in groups in this field will be transferred "
        "to the 'Access Users' field. Keep in mind that removing "
        "groups will not  remove users from 'Access Users' field.",
    )

    @api.onchange("access_group_ids")
    def _onchange_access_groups(self):
        for pricelist in self:
            pricelist.access_user_ids |= pricelist.access_group_ids.mapped("users")
