from odoo_somconnexio_python_client.client import Client


class Category:
    def __init__(self, reference, name, childs, breadcrumb=[], **kwargs):
        self.ref = reference
        self.name = name
        self.type = "category"
        self.children = [
            Category(**child, breadcrumb=[reference])
            for child in childs
            if child["type"] == "category"
        ]
        self.pages = [
            {
                "ref": child["reference"],
                "name": child["name"],
                "breadcrumb": [child["reference"], reference] + breadcrumb,
            }
            for child in childs
            if child["type"] == "content"
        ]


class Page:
    def __init__(self, reference, name, content, parent_reference, tags, **kwargs):
        self.ref = reference
        self.name = name
        self.type = "page"
        self.content = content
        self.category = parent_reference
        self.tags = tags


class SearchResult:
    def __init__(self, reference, name, tags, breadcrumb, **kwargs):
        self.ref = reference
        self.name = name
        self.type = "page"
        self.tags = tags
        self.breadcrumb = breadcrumb["references"]


class Knowledge:
    _url_base_path = "/knowledge"
    _url_categories_path = "categories"
    _url_page_path = "page"
    _url_highlighted_path = "highlighted"
    _url_search_path = "search"

    def __init__(self, url_resource_path, lang):
        self.response_data = Client().get(
            "{base}/{resource}".format(
                base=self._url_base_path, resource=url_resource_path
            ),
            # Review _ES in lang. Now we are managing it in other way. Product-catalog example
            {"lang": "{}_ES".format(lang)},
            secondary_domain=True,
        )

    @classmethod
    def get_categories(cls, lang="ca"):
        response_data = cls(cls._url_categories_path, lang).response_data
        if not response_data:
            return []

        return [Category(**data) for data in response_data]

    @classmethod
    def get_category(cls, category_ref, lang="ca"):
        url_resource_path = "{resource}/{ref}".format(
            resource=cls._url_categories_path, ref=category_ref
        )

        response_data = cls(url_resource_path, lang).response_data
        if not response_data:
            raise Exception("Category not found")

        return Category(**response_data[0])

    @classmethod
    def get_pages_by_highlight(cls, highlight_code, lang="ca"):
        url_resource_path = "{resource}/{code}".format(
            resource=cls._url_highlighted_path, code=highlight_code
        )

        response_data = cls(url_resource_path, lang).response_data
        if not response_data:
            return []

        return [Page(**datum) for datum in response_data]

    @classmethod
    def search_pages(cls, pattern, lang="ca"):
        url_resource_path = "{resource}/{pattern}".format(
            resource=cls._url_search_path,
            pattern=pattern,
        )

        response_data = cls(url_resource_path, lang).response_data
        if not response_data:
            return []

        return [SearchResult(**datum) for datum in response_data]

    @classmethod
    def get_page(cls, page_ref, lang="ca"):
        url_resource_path = "{resource}/{ref}".format(
            resource=cls._url_page_path, ref=page_ref
        )

        response_data = cls(url_resource_path, lang).response_data
        if not response_data:
            raise Exception("Page not found")

        return Page(**response_data)
