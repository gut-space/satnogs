from threading import local
from typing import Any
import unittest
from unittest import mock

import flask

from app import app
from app.pagination import Pagination, use_pagination

class TestPagination(unittest.TestCase):

    def test_limit_and_offset(self):
        items_per_page = 5
        paginaton = Pagination(items_per_page)

        limit_and_offset = paginaton.limit_and_offset(1)
        self.assertLessEqual({
            'limit': 5,
            'offset': 0
        }.items(), limit_and_offset.items())

        limit_and_offset = paginaton.limit_and_offset(2)
        self.assertLessEqual({
            'limit': 5,
            'offset': 5
        }.items(), limit_and_offset.items())

        limit_and_offset = paginaton.limit_and_offset(3)
        self.assertLessEqual({
            'limit': 5,
            'offset': 10
        }.items(), limit_and_offset.items())

        limit_and_offset = paginaton.limit_and_offset(4)
        self.assertLessEqual({
            'limit': 5,
            'offset': 15
        }.items(), limit_and_offset.items())

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

    @mock.patch('flask.templating._render', return_value='')
    def test_use_pagination_single(self, mock_render):

        received_limit_and_offset = None

        with app.test_client() as client:
            @app.route("/test-single-pagination")
            @use_pagination(10)
            def pagination_single(limit_and_offset):
                nonlocal received_limit_and_offset              
                received_limit_and_offset = limit_and_offset
                return 'index.html', dict(item_count=100)
            response = client.get("/test-single-pagination",
                query_string=dict(page=3))

            self.assertTrue(mock_render.called)
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(received_limit_and_offset)
            self.assertDictEqual({ 'limit': 10, 'offset': 20},
                received_limit_and_offset) # type: ignore

            _, context, _ = mock_render.call_args[0]
            self.assertTrue("pagination" in context)
            self.assertEqual(context["pagination"]["items_count"], 100)

    @mock.patch('flask.templating._render', return_value='')
    def test_use_pagination_multiple(self, mock_render):

        received_limit_and_offset: Any = None

        with app.test_client() as client:
            @app.route("/test-multi-pagination")
            @use_pagination(10, {
                'items_per_page': 50,
                'count_name': 'item_a_count',
                'page_param': 'page_a',
                'template_arg_name': 'pagination_a'
            },
            {
                'items_per_page': 50,
                'count_name': 'item_b_count',
                'page_param': 'page_b',
                'template_arg_name': 'pagination_b'
            })
            def pagination_multiple(limit_and_offset):
                nonlocal received_limit_and_offset              
                received_limit_and_offset = limit_and_offset
                return 'index.html', dict(item_a_count=100, item_b_count=200)
            response = client.get("/test-multi-pagination",
                query_string=dict(page_a=3))

            self.assertTrue(mock_render.called)
            self.assertEqual(response.status_code, 200)
    
            self.assertIsNotNone(received_limit_and_offset)
            limit_and_offset_a, limit_and_offset_b = received_limit_and_offset
            self.assertDictEqual({ 'limit': 50, 'offset': 100},
                limit_and_offset_a) # type: ignore
            self.assertDictEqual({ 'limit': 50, 'offset': 0},
                limit_and_offset_b) # type: ignore

            _, context, _ = mock_render.call_args[0]
            self.assertTrue("pagination_a" in context)
            self.assertTrue("pagination_b" in context)
            self.assertEqual(context["pagination_a"]["items_count"], 100)
            self.assertEqual(context["pagination_b"]["items_count"], 200)
