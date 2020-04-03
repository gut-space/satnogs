'''
Pagination helpers. You have three ways to use this tools:

1. Low-level. You should create Paginate class object and use them to calculate
    all needed parameters. You must manuall retrive page number and pass
    pagination variables to template
2. Medium-level. See "use_page" decorator docstring. It provides ready solutions
    for common tasks, but you need to join it together.
3. High-level. See "use_pagination" decorator docstring. It does most tasks
    for you. You get ready parameters for your repository read method and you
    need only retrive item count.
'''

from functools import wraps
import math
from typing import Optional
import urllib.parse as urlparse
import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

import webargs
from webargs.flaskparser import use_kwargs
from flask import request
from flask.templating import render_template

from app import app

# URL query parameter name where page number will be stored.
PARAM_NAME = "page"

class LimitAndOffsetDict(TypedDict):
    limit: int
    offset: int

class PaginationDict(TypedDict):
    page_count: int
    page_current: int
    url: str
    items_count: int
    items_current: int

class TemplatePaginationDict(TypedDict):
    pagination: PaginationDict

class Pagination:
    '''Helper class. It is responsible for all calculations related
       to pagination.'''

    def __init__(self, items_per_page:Optional[int]=None):
        '''items_per_page defines how many item should be display on one page.
            If it is None then value will be read from configuration'''
        if items_per_page is None:
            items_per_page = int(app.config["view"]["items_per_page"])
        self.items_per_page: int = items_per_page

    @staticmethod
    def _current_url() -> str:
        '''Retrive current URL from request. Throw exception if request doesn't
            exist'''
        return request.url

    @staticmethod
    def _current_page(url: str) -> int:
        '''Retrive page number from URL query parameters. If parameter isn't
        included or it is less then 1 then we assume that it is first page'''
        _, _, _, query, _ = urlparse.urlsplit(url)
        params = urlparse.parse_qs(query)
        pages = params.get(PARAM_NAME, None)
        if pages is None :
            return 1
        page = int(pages[0])
        if page < 1:
            return 1
        return page

    def _page_count(self, item_count: int) -> int:
        '''Calculate total page count from total item count'''
        return int(math.ceil(item_count / self.items_per_page))

    def _page_item_count(self, item_count: int, page: int) -> int:
        '''Calculate item count on specific page. All pages without last have
        item count equals self.items_per_page.'''
        return min(
            max(
                item_count - (page - 1) * self.items_per_page,
                0
            ),
            self.items_per_page
        )

    def limit_and_offset(self, page: int) -> LimitAndOffsetDict:
        '''Return limit and offset for SQL query for specific page'''
        return {
            'limit': self.items_per_page,
            'offset': self.items_per_page * (page - 1)
        }

    def _template_parameters(self, item_count: int,
            url: Optional[str]=None, page:Optional[int]=None) -> PaginationDict:
        '''Return parameters for paginate template.'''
        url = Pagination._current_url() if url is None else url
        if page is None:
            current = Pagination._current_page(url)
        else:
            current = page
        return {
            'url': url,
            'page_current': current,
            'page_count': self._page_count(item_count),
            'items_count': item_count,
            'items_current': self._page_item_count(item_count, current)

        }

    def template_kwargs(self, item_count: int,
            url: Optional[str]=None, page:Optional[int]=None
        )-> TemplatePaginationDict:
        '''Return parameters for pagination template bounded with dict with
            expected key name by template'''
        return {
            'pagination': self._template_parameters(
                item_count, url, page
            )
        }

def use_page(f):
    '''
    Decorator for retrive page number from request. Part of medium-level
    pagination solution.

    Checklist (what you need to do to use it correctly):
    1. Add this decorator to your action (without parenthness)
    2. Take as function argument "page"
    3. Create object of Pagination class
    4. Calculate limit and offset
    5. Pass limit and offset to specific repository read method by unpack
        content by duble asteriks
    6. Fetch total count of your items
    7. Create template pagination arguments
    8. Pass template arguments by unpack it using double asteriks
        to "render_template" function
    9. Include "paginate.html" template in your template

    Example
    =======
    >>> # In action .py file. In comments are checklist steps.
    >>> # 1. Use decorator
        @use_page
        # 2. Take parameter
        def obslist(page: int):
            # 3. Create pagination object
            pagination = Pagination()
            ...
            # 4. Calculate limit and offset
            limit_and_offset = pagination.limit_and_offset(page)
            # 5. Pass limit and offset to read item method
            items = repo.read_items(**limit_and_offset)
            # 6. Fetch item count
            count = repo.count_items()
            # 7. Create template arguments dict
            p_args = pagination.template_kwargs(observation_count)
            # 8. Pass template arguments
            return render_template('template.html', items=items, **p_args)

    >>> # 9. Include pagination template in your .html template file
    >>> {% include 'pagination.html' %}
    '''
    return use_kwargs({
        PARAM_NAME: webargs.fields.Int(missing=1, 
            validate=webargs.validate.Range(min=1))
    })(f)

def use_pagination(items_per_page:Optional[int]=None,
        item_count_argname="item_count"):
    '''
    High-level pagination helper. It automatically retrive page number,
    compute limit and offset for SQL query and at end append pagination template
    arguments.

    Checklist (what you need to do to use it correctly):
    1. Add this decorator to your action (with parenthness)
    2. Take as function argument "limit_and_offset"
    3. Pass limit and offset to specific repository read method by unpack
        content by duble asteriks
    4. Fetch total count of your items
    5. When return from action don't call "render_template" at end.
        Instead of this returns tuple of "render_template" arguments.
        Your tuple should have two items. First is template name or list and
        second is context (template parameters.)
    6. In context include "item_count" (customize it using
        "item_count_argname") with total count of your items
    7. Include "paginate.html" template in your template

    Parameters
    ==========
    items_per_page: int, optional
        Numer of items on single page. Must be greater than 1. If it is None
        then value will be read from configuration (section: view, parameter:
        items_per_page)
    item_count_argname: str, optional
        Name of argument with total item count. Argument with this name must
        be pass in context by decorated function.

    Example
    =======
    >>> # In action .py file. On right side are checklist steps.
    >>> @use_pagination()                                  #1 decorator
        def action(limit_and_offset):                      #2 shift for query
            ...
            items = repo.read_items(**limit_and_offset) #3 pass limit and offset
            count = repo.count_items()                     #4 count items

            return 'action.html', dict(items=items, #5 don't use render_template
                                       item_count=count)   #6 include item_count

    >>> # Somewhere in action .html template. 
    >>> {% include 'pagination.html' %}                    #7 include pagination
    '''
    def use_pagination_decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            page = kwargs[PARAM_NAME]
            del kwargs[PARAM_NAME]

            pagination = Pagination(items_per_page=items_per_page)
            limit_and_offset = pagination.limit_and_offset(page)
            template, context = f(*args, **kwargs, 
                limit_and_offset=limit_and_offset)
            item_count = context[item_count_argname]
            pagination_kwargs = pagination.template_kwargs(item_count,
                page=page)
            return render_template(template, **context, **pagination_kwargs)

        decorated_wrapper = use_page(wrapped)
        return decorated_wrapper
    return use_pagination_decorator
