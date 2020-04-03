import unittest
from app.pagination import Pagination, PaginationDict

class TestPagination(unittest.TestCase):

    def test_limit_and_offset(self):
        items_per_page = 5
        paginaton = Pagination(items_per_page)

        limit_and_offset = paginaton.limit_and_offset(1)
        self.assertDictContainsSubset({
            'limit': 5,
            'offset': 0
        }, limit_and_offset)

        limit_and_offset = paginaton.limit_and_offset(2)
        self.assertDictContainsSubset({
            'limit': 5,
            'offset': 5
        }, limit_and_offset)

        limit_and_offset = paginaton.limit_and_offset(3)
        self.assertDictContainsSubset({
            'limit': 5,
            'offset': 10
        }, limit_and_offset)

        limit_and_offset = paginaton.limit_and_offset(4)
        self.assertDictContainsSubset({
            'limit': 5,
            'offset': 15
        }, limit_and_offset)

    def test_items_current(self):
        items = 15
        items_per_page = 5
        pagination = Pagination(items_per_page)
        current = lambda p: pagination.template_kwargs(
                items, url="http://example.com", page=p
            )["pagination"]["items_current"]

        self.assertEqual(current(1), 5)
        self.assertEqual(current(2), 5)
        self.assertEqual(current(3), 5)
        self.assertEqual(current(4), 0)

        