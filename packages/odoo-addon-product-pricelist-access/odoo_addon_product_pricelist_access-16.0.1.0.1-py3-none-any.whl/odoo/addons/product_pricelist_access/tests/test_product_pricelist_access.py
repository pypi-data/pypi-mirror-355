# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestProductPricelistAccess(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist-Test",
            }
        )
        cls.pricelist_item = cls.env["product.pricelist.item"].create(
            {
                "pricelist_id": cls.pricelist.id,
                "applied_on": "3_global",
                "compute_price": "fixed",
                "fixed_price": 100.0,
            }
        )
        cls.test_user_1 = cls.env["res.users"].create(
            {
                "name": "Test User-1",
                "login": "test_user_1",
            }
        )
        cls.test_user_2 = cls.env["res.users"].create(
            {
                "name": "Test User-2",
                "login": "test_user_2",
            }
        )
        cls.restrict_pricelist_group = cls.env.ref(
            "product_pricelist_access.restrict_product_pricelist"
        )
        cls.test_user_1.groups_id |= cls.restrict_pricelist_group
        cls.test_user_2.groups_id |= cls.restrict_pricelist_group
        cls.extra_group = cls.env["res.groups"].create({"name": "Exra-Group"})
        cls.test_user_2.groups_id |= cls.extra_group

    def test_product_pricelist_user_access(self):
        pricelist = self.pricelist.with_user(self.test_user_1.id)
        pricelist.check_access_rule("read")
        pricelist = self.pricelist.with_user(self.test_user_2.id)
        pricelist.check_access_rule("read")
        self.pricelist.access_user_ids = [self.test_user_1.id]
        pricelist = self.pricelist.with_user(self.test_user_1.id)
        pricelist.check_access_rule("read")
        pricelist = self.pricelist.with_user(self.test_user_2.id)
        with self.assertRaises(AccessError):
            pricelist.check_access_rule("read")
        self.pricelist.access_user_ids = self.pricelist.access_user_ids.ids + [
            self.test_user_2.id
        ]
        pricelist.check_access_rule("read")

    def test_product_pricelist_group_onchange(self):
        self.pricelist.access_group_ids |= self.extra_group
        self.pricelist._onchange_access_groups()
        self.assertTrue(self.test_user_2.id in self.pricelist.access_user_ids.ids)
        self.assertFalse(self.test_user_1.id in self.pricelist.access_user_ids.ids)
        self.pricelist.access_group_ids |= self.restrict_pricelist_group
        self.pricelist._onchange_access_groups()
        self.assertTrue(self.test_user_2.id in self.pricelist.access_user_ids.ids)
        self.assertTrue(self.test_user_1.id in self.pricelist.access_user_ids.ids)
        self.pricelist.access_group_ids = self.extra_group
        self.assertTrue(self.test_user_2.id in self.pricelist.access_user_ids.ids)
        self.assertTrue(self.test_user_1.id in self.pricelist.access_user_ids.ids)

    def test_product_pricelist_item_access(self):
        pricelist_item = self.pricelist_item.with_user(self.test_user_1.id)
        pricelist_item.check_access_rule("read")
        pricelist_item = self.pricelist_item.with_user(self.test_user_2.id)
        pricelist_item.check_access_rule("read")
        self.pricelist.access_user_ids = [self.test_user_1.id]
        pricelist_item = self.pricelist_item.with_user(self.test_user_1.id)
        pricelist_item.check_access_rule("read")
        pricelist_item = self.pricelist_item.with_user(self.test_user_2.id)
        with self.assertRaises(AccessError):
            pricelist_item.check_access_rule("read")
        self.pricelist.access_user_ids = self.pricelist.access_user_ids.ids + [
            self.test_user_2.id
        ]
        pricelist_item = self.pricelist_item.with_user(self.test_user_1.id)
        pricelist_item.check_access_rule("read")
        pricelist_item = self.pricelist_item.with_user(self.test_user_2.id)
        pricelist_item.check_access_rule("read")
