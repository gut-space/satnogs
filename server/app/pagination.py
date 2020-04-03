import math
import urllib.parse as urlparse

from flask import request

ITEMS_PER_PAGE = 100

def get_limit_and_offset(page: int):
    return {
        'offset': ITEMS_PER_PAGE * (page - 1),
        'limit': ITEMS_PER_PAGE
    }

def get_page_count(item_count: int):
    return int(math.ceil(item_count / ITEMS_PER_PAGE))

def _get_current_url():
    return request.url

def _get_current_page(url: str, param_name) -> int:
    _, _, _, query, _ = urlparse.urlsplit(url)
    params = urlparse.parse_qs(query)
    pages = params.get(param_name, None)
    if pages is None:
        return 1
    else:
        return int(pages[0])

def paginate(item_count: int, param_name="page", url=None):
    url = _get_current_url() if url is None else url
    return {
        'url': url,
        'current': _get_current_page(url, param_name),
        'count': get_page_count(item_count)
    }
