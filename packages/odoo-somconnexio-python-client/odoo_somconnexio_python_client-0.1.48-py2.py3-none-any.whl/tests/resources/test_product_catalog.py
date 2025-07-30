from __future__ import unicode_literals  # support both Python2 and 3

import pytest
import unittest2 as unittest

from odoo_somconnexio_python_client.resources.product_catalog import (
    Offer,
    Product,
    ProductCatalog,
    Pack,
)


class TariffTests(unittest.TestCase):
    @pytest.mark.vcr()
    def test_search_code(self):
        pricelists = ProductCatalog.search(code="21IVA")
        tariff_names = []
        tariff_codes = []
        tariff_available_for = []
        tariff_offer = None

        pricelist_21IVA = pricelists[0]
        self.assertIsInstance(pricelist_21IVA, ProductCatalog)
        self.assertEqual(pricelist_21IVA.code, "21IVA")
        for product in pricelist_21IVA.products:
            self.assertIsInstance(product, Product)
            tariff_names.append(product.name)
            tariff_codes.append(product.code)
            tariff_available_for.append(product.available_for)
            if product.code == "SE_SC_REC_MOBILE_T_UNL_30720":
                tariff_offer = product.offer

        self.assertIn("ADSL sense fix", tariff_names)
        self.assertIn("SE_SC_REC_BA_F_100", tariff_codes)
        self.assertIn(["member"], tariff_available_for)

        self.assertIsInstance(tariff_offer, Offer)
        self.assertIn("SE_SC_REC_MOBILE_PACK_UNL_30720", tariff_offer.code)
        self.assertIn("Il·limitades 30 GB (Pack)", tariff_offer.name)
        self.assertEqual(1.0, tariff_offer.price)

        adsl_wo_fix_product = list(
            filter(lambda p: p.code == "SE_SC_REC_BA_ADSL_SF", pricelist_21IVA.products)
        )
        self.assertEqual(len(adsl_wo_fix_product), 1)
        self.assertFalse(adsl_wo_fix_product[0].has_landline_phone)

        fiber100_with_fix_product = list(
            filter(lambda p: p.code == "SE_SC_REC_BA_F_100", pricelist_21IVA.products)
        )
        self.assertEqual(len(fiber100_with_fix_product), 1)
        self.assertTrue(fiber100_with_fix_product[0].has_landline_phone)

        self.assertTrue(pricelist_21IVA.packs)

        pack_codes = []
        pack_names = []
        pack_tariff_names = []
        pack_tariff_codes = []
        pack_mobiles_in_pack = []
        pack_fiber_bandwidth = []

        for pack in pricelist_21IVA.packs:
            self.assertIsInstance(pack, Pack)
            pack_codes.append(pack.code)
            pack_names.append(pack.name)
            pack_mobiles_in_pack.append(pack.mobiles_in_pack)
            pack_fiber_bandwidth.append(pack.fiber_bandwidth)
            for product in pack.products:
                self.assertIsInstance(product, Product)
                pack_tariff_names.append(product.name)
                pack_tariff_codes.append(product.code)

        self.assertIn("SE_SC_REC_PACK_FIBER_100_UNL_20480", pack_codes)
        self.assertIn("Fibra 1Gb + Fix + 50 GB compartides 2 mòbils", pack_names)
        self.assertIn("Fibra 300Mb Sense Fix", pack_tariff_names)
        self.assertIn("SE_SC_REC_MOBILE_PACK_UNL_20480", pack_tariff_codes)
        self.assertIn(2, pack_mobiles_in_pack)
        self.assertIn(100, pack_fiber_bandwidth)

    @pytest.mark.vcr()
    def test_search_non_existant_code(self):
        pricelists = ProductCatalog.search(code="BBBB")
        self.assertEqual(len(pricelists), 0)

    @pytest.mark.vcr()
    def test_search_code_with_category_filter(self):
        pricelists = ProductCatalog.search(code="21IVA", category="mobile")
        tariff_codes = []

        pricelist_21IVA = pricelists[0]
        for product in pricelist_21IVA.products:
            tariff_codes.append(product.code)
            self.assertEqual(product.category, "mobile")

        self.assertNotIn("SE_SC_REC_BA_F_100", tariff_codes)
        self.assertIn("SE_SC_REC_MOBILE_T_0_0", tariff_codes)

    @pytest.mark.vcr()
    def test_search_catalog_with_lang(self):
        ca_pricelists = ProductCatalog.search(code="21IVA", lang="ca")
        es_pricelists = ProductCatalog.search(code="21IVA", lang="es")
        ca_product_names = [p.name for p in ca_pricelists[0].products]
        es_product_names = [p.name for p in es_pricelists[0].products]

        self.assertIn("Il·limitades 30 GB", ca_product_names)
        self.assertIn("Ilimitadas 30 GB", es_product_names)

    @pytest.mark.vcr()
    def test_get_by_product_code(self):
        """For product fibra 100Mb only are available other Fiber products."""
        pricelists = ProductCatalog.get_by_product_code(
            product_code="SE_SC_REC_BA_F_100"
        )
        product_codes = [p.code for p in pricelists[0].products]

        self.assertIn("SE_SC_REC_BA_F_100_SF", product_codes)

    @pytest.mark.vcr()
    def test_search_company_catalog(self):
        pricelists = ProductCatalog.search(is_company="true")
        product_codes = [p.code for p in pricelists[0].products]
        pack_codes = [p.code for p in pricelists[0].packs]

        self.assertIn("SE_SC_REC_MOBILE_T_UNL_30720", product_codes)
        self.assertIn("SE_SC_REC_PACK_FIBER_1000_2_MOBILES_50", pack_codes)
