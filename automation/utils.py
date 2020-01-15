COMMENT_PASS_TAG = "SatNOG-PG-Pass"
COMMENT_PLAN_TAG = "SatNOG-PG-Plan"

def first(iterable, condition = lambda x: True):
    """
    Returns the first item in the `iterable` that
    satisfies the `condition`.

    If the condition is not given, returns the first item of
    the iterable.

    Return `None` if no item satysfing the condition is found.

    >>> first( (1,2,3), condition=lambda x: x % 2 == 0)
    2
    >>> first(range(3, 100))
    3
    >>> first( () )
    None
    """
    try:
        return next(x for x in iterable if condition(x))
    except StopIteration:
        return None