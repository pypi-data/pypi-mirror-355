from odoo_somconnexio_python_client.resources.contract import Contract


class MultimediaContract(Contract):
    _url_path = "/contract/multimedia"

    def __init__(self, subscription_code, **kwargs):
        super().__init__(**kwargs)
        self.subscription_code = subscription_code

    @classmethod
    def search_by_customer_ref(
        cls,
        customer_ref,
    ):
        """
        Search Multimedia Contracts in Odoo by partner's ref

        :return: Contracts objects if exists
        """
        params = {"partner_ref": customer_ref}
        return cls._get(
            params=params,
        )
