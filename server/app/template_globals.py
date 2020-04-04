from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

from app import app
from app.utils import first

@app.template_global()
def url_page(url: str, page: int, param_name: str):
    """Given a URL, set or replace a query parameter and return the
    modified URL.

    See: https://stackoverflow.com/a/12897375
    >>> set_query_parameter('http://example.com?foo=bar&biz=baz', 'foo', 'stuff')
    'http://example.com?foo=stuff&biz=baz'

    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qsl(query_string)
    
    page_param = first(lambda p: p[0] == param_name, query_params)
    if page_param is not None:
        query_params.remove(page_param)
    query_params.append((param_name, str(page)))
    
    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment)) # type: ignore
