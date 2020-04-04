'''
Pagination helpers. You have three ways to use this tools:

1. Low-level. You should create Paginate class object and use them to calculate
    all needed parameters. You must manually retrieve page number and pass
    pagination variables to template
2. Medium-level. See "use_page" decorator docstring. It provides ready solutions
    for common tasks, but you need to join it together.
3. High-level. See "use_pagination" decorator docstring. It does most tasks
    for you. You get ready parameters for your repository read method and you
    need only retrive item count.
'''

from functools import wraps
import math
from typing import Iterable, List, Optional, Sequence, Sized, Tuple, Union
import urllib.parse as urlparse
import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

import webargs
from webargs.flaskparser import use_kwargs
from flask import request
from flask import render_template

from app import app

class LimitAndOffsetDict(TypedDict):
    limit: int
    offset: int

class PaginationDict(TypedDict):
    page_count: int
    page_current: int
    url: str
    items_count: int
    items_current: int
    param: str

class Pagination:
    '''Helper class. It is responsible for all calculations related
       to pagination.'''

    def __init__(self, items_per_page:Optional[int]=None, param_name:str="page"):
        '''items_per_page defines how many item should be display on one page.
            If it is None then value will be read from configuration'''
        if items_per_page is None:
            items_per_page = int(app.config["view"]["items_per_page"])
        self.items_per_page: int = items_per_page
        self.param_name = param_name

    @staticmethod
    def _current_url() -> str:
        '''Retrive current URL from request. Throw exception if request doesn't
            exist'''
        return request.url

    def _current_page(self, url: str) -> int:
        '''Retrive page number from URL query parameters. If parameter isn't
        included or it is less then 1 then we assume that it is first page'''
        _, _, _, query, _ = urlparse.urlsplit(url)
        params = urlparse.parse_qs(query)
        pages = params.get(self.param_name, None)
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
            current = self._current_page(url)
        else:
            current = page
        return {
            'url': url,
            'page_current': current,
            'page_count': self._page_count(item_count),
            'items_count': item_count,
            'items_current': self._page_item_count(item_count, current),
            'param': self.param_name
        }

    def template_kwargs(self, item_count: int,
            url: Optional[str]=None, page:Optional[int]=None,
            template_arg:str='pagination'):
        '''Return parameters for pagination template bounded with dict with
            expected key name by template'''
        return {
            template_arg: self._template_parameters(
                item_count, url, page
            )
        }

def use_page(*param_names:Iterable[str]):
    def use_page_decorator(f):
        '''
        Decorator for retrive page number from request. Part of medium-level
        pagination solution.

        Checklist (what you need to do to use it correctly):
        1. Add this decorator to your action (with parenthness)
        2. Take as function argument "page"
        3. Create object of Pagination class
        4. Calculate limit and offset
        5. Pass limit and offset to specific repository read method by unpack
            content by double asterisks
        6. Fetch total count of your items
        7. Create template pagination arguments
        8. Pass template arguments by unpack it using double asteriks
            to "render_template" function
        9. Include "paginate.html" template in your template

        Parameters
        ==========
        param_name: str, optional
            Request query parameter name with page number

        Example
        =======
        >>> # In action .py file. In comments are checklist steps.
        >>> # 1. Use decorator
            @use_page()
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
        argmap = {}
        for param_name in param_names:
            argmap[param_name] = webargs.fields.Int(missing=1, 
                validate=webargs.validate.Range(min=1))
        return use_kwargs(argmap)(f)
    return use_page_decorator

class PaginationConfiguration(TypedDict):
    '''
    count_name: key name of context entry with item count returned from action
    page_param: HTTP query parameter name with page number
    template_arg_name: name of pagination parameter inserted to context to
        access in template
    '''
    items_per_page: Optional[int]
    count_name: str
    page_param: str
    template_arg_name: str

PaginationConfigurationSingleOrMany=Union[PaginationConfiguration,
                                          Iterable[PaginationConfiguration]]
ItemsPerPageOrPaginationConfig = Union[
        Optional[int],
        PaginationConfiguration
]
def use_pagination(
        per_page_or_config: Optional[ItemsPerPageOrPaginationConfig]=None,
        *args: PaginationConfiguration):
    '''
    High-level pagination helper. It automatically retrive page number,
    compute limit and offset for SQL query and at end append pagination template
    arguments.
    You may define one or multiple pagination on the same page.

    Checklist (what you need to do to use it correctly):
    1. Add this decorator to your action (with parenthness)
    2. Take as function argument "limit_and_offset"
    3. Pass limit and offset to specific repository read method by unpack
        content by double asterisks
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
    per_page_or_config: int or PaginationConfiguration
        Numer of items on single page. Must be greater than 1. If it is None
        then value will be read from configuration (section: view, parameter:
        items_per_page). Or PaginationConfiguration.
    *args: Sequence of PaginationConfiguration, optional
        List of pagination configuration for handle multiple configurations
        in the same time. When it is provided then you should avoid pass as
        first argument an integer, because it doesn't affect.

    Example
    =======
    >>> # Single pagination
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

    >>> # Many pagination
    >>> # In action .py file. On right side are checklist steps.
    >>> @use_pagination(                                   #1 decorator
            {
                'items_per_page': 5,
                'count_name': 'item_a_count',
                'page_param': 'page_a',
                'template_arg_name': 'pagination_a'
            },
            {
                'items_per_page': None,
                'count_name': 'item_b_count',
                'page_param': 'page_b',
                'template_arg_name': 'pagination_b'
            }
        )
        def action(limit_and_offset):         #2 shift for query, now it is list
            ...
            limit_and_offset_a, limit_and_offset_b = limit_and_offset
            a_items = repo.read_a_items(**limit_and_offset_a) #3 limit and offset
            b_items = repo.read_b_items(**limit_and_offset_b)
            count_a = repo.count_a_items()                     #4 count items
            count_b = repo.count_b_items()
            ...
            return 'action.html', dict(items=items, #5 don't use render_template
                                    item_a_count=count_a, #6 include counts
                                    item_b_count=count_b)

    >>> # Somewhere in action .html template.
    >>> {% with pagination = pagination_a %}            #7 include pagination
        {% include 'pagination.html' %}
        {% endwith %}
        {% with pagination = pagination_b %}
        {% include 'pagination.html' %}
        {% endwith %}
    '''
    configurations: Sequence[PaginationConfiguration]
    items_per_page: Optional[int] = None
    
    if type(per_page_or_config) == int:
        items_per_page = per_page_or_config # type: ignore
        configurations = args
    elif per_page_or_config is not None :
        configurations = [per_page_or_config, *args] # type: ignore
    else:
        configurations = args

    if len(configurations) == 0:
        config: PaginationConfiguration = {
            "count_name": "item_count",
            "page_param": "page",
            "template_arg_name": "pagination",
            "items_per_page": items_per_page
        }
        configurations = (config,)

    is_single_configuration = len(configurations) == 1

    def use_pagination_decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            pages: List[int] = []
            for config in configurations:
                page = kwargs[config["page_param"]]
                del kwargs[config["page_param"]]
                pages.append(int(page))

            paginations = [Pagination(items_per_page=c["items_per_page"],
                                      param_name=c["page_param"])
                            for c in configurations]
            many_lao = [pagination.limit_and_offset(page) 
                for page, pagination in zip(pages, paginations)]
            limit_and_offset = many_lao[0] if is_single_configuration else many_lao

            template, context = f(*args, **kwargs, 
                limit_and_offset=limit_and_offset)

            item_counts = [context[c["count_name"]] for c in configurations]
            pagination_kwargs = {}
            for pagination, item_count, page, config in zip(paginations,
                                            item_counts, pages, configurations):
                kwargs = pagination.template_kwargs(item_count,
                    page=page, template_arg=config["template_arg_name"])
                pagination_kwargs.update(kwargs)
            return render_template(template, **context, **pagination_kwargs)

        param_names = [c["page_param"] for c in configurations]
        decorator = use_page(*param_names)
        decorated_wrapper = decorator(wrapped)
        return decorated_wrapper
    return use_pagination_decorator
