import pytest
import unittest2 as unittest

from odoo_somconnexio_python_client.resources.knowledge import Knowledge


class KnowledgeTests(unittest.TestCase):
    @pytest.mark.vcr()
    def test_get_categories(self):
        categories = Knowledge.get_categories()
        self._assert_category(categories[1])

    @pytest.mark.vcr()
    def test_get_categories_not_found(self):
        assert Knowledge.get_categories() == []

    @pytest.mark.vcr()
    def test_get_category(self):
        category = Knowledge.get_category("test")
        self._assert_category(category)

    @pytest.mark.vcr()
    def test_get_category_not_found(self):
        self.assertRaises(
            Exception,
            Knowledge.get_category,
            category_ref="dummy",
        )

    @pytest.mark.vcr()
    def test_get_pages_by_highlight(self):
        pages = Knowledge.get_pages_by_highlight("test")
        self._assert_page(pages[0])

    @pytest.mark.vcr()
    def test_get_pages_by_highlight_not_found(self):
        assert Knowledge.get_pages_by_highlight("dummy") == []

    @pytest.mark.vcr()
    def test_search_pages(self):
        pages = Knowledge.search_pages("search")
        self._assert_search_page(pages[0])

    @pytest.mark.vcr()
    def test_lang_search_pages(self):
        pages = Knowledge.search_pages("busqueda", "es")
        self._assert_search_page(pages[0])

    @pytest.mark.vcr()
    def test_search_pages_not_found(self):
        assert Knowledge.search_pages("dummy") == []

    @pytest.mark.vcr()
    def test_get_page(self):
        page = Knowledge.get_page("test_test")
        self._assert_page(page)

    @pytest.mark.vcr()
    def test_get_page_not_found(self):
        self.assertRaises(
            Exception,
            Knowledge.get_page,
            page_ref="dummy",
        )

    def _assert_category(self, cat):
        assert cat.ref == "test"
        assert cat.name == "Test"
        assert cat.type == "category"
        assert cat.children[0].ref == "test_child_cat"
        assert cat.children[0].name == "Test child cat"
        assert cat.children[0].type == "category"
        assert cat.children[0].pages == []
        assert cat.pages[0]["ref"] == "test_test"
        assert cat.pages[0]["name"] == "Test"
        assert cat.pages[0]["breadcrumb"] == ["test_test", "test"]

    def _assert_page(self, page):
        assert page.ref == "test_test"
        assert page.name == "Test"
        assert page.type == "page"
        assert page.content == "<p>Content</p><p>search_test<br></p>"
        assert page.category == "test"
        assert page.tags == []

    def _assert_search_page(self, page):
        assert page.ref == "test_test"
        assert page.name == "Test"
        assert page.type == "page"
        assert page.tags == []
        assert page.breadcrumb == ["test_test", "test"]
