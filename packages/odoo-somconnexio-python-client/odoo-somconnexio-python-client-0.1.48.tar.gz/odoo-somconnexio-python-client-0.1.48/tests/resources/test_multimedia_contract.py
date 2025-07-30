import pytest
import unittest2 as unittest

from odoo_somconnexio_python_client.exceptions import (
    ResourceNotFound,
)
from odoo_somconnexio_python_client.resources.multimedia_contract import (
    MultimediaContract,
)


class ContractTests(unittest.TestCase):
    @pytest.mark.vcr()
    def test_search_resource_not_found(self):
        self.assertRaises(
            ResourceNotFound,
            MultimediaContract.search_by_customer_ref,
            customer_ref="9999",
        )

    @pytest.mark.vcr()
    def test_search_resource_found(self):
        contracts = MultimediaContract.search_by_customer_ref(customer_ref="1234")
        contract = contracts[0]
        assert contract.subscription_code == "FLM0003"
