import functools
import time
from itertools import zip_longest
from typing import Iterator

from .error import CAPIError, VMError


def timeout(func):
    """
    Times out the login function once time elapsed exceeds remote.timeout.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        remote, *_ = args
        func(*args, **kwargs)

        err = None
        start = time.time()
        while time.time() < start + remote.timeout:
            try:
                time.sleep(0.1)  # ensure at least 0.1 delay before clearing dirty
                remote.logger.info(
                    f'{type(remote).__name__}: Successfully logged into {remote} version {remote.version}'
                )
                remote.logger.debug(f'login time: {round(time.time() - start, 2)}')
                err = None
                break
            except CAPIError as e:
                err = e
                continue
        if err:
            raise VMError('Timeout logging into the api')
        remote.clear_dirty()

    return wrapper


def polling(func):
    """
    Offers memoization for a set into get operation.

    If sync clear dirty parameters before fetching new value.

    Useful for loop getting if not running callbacks
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        get = func.__name__ == 'get'
        mb_get = func.__name__ == 'get_buttonstatus'
        remote, *remaining = args

        if get:
            param, *rem = remaining
        elif mb_get:
            id, mode, *rem = remaining
            param = f'mb_{id}_{mode}'

        if param in remote.cache:
            return remote.cache.pop(param)
        if remote.sync:
            remote.clear_dirty()
        return func(*args, **kwargs)

    return wrapper


def script(func):
    """Convert dictionary to script"""

    def wrapper(*args):
        remote, script = args
        if isinstance(script, dict):
            params = ''
            for key, val in script.items():
                obj, m2, *rem = key.split('-')
                index = int(m2) if m2.isnumeric() else int(*rem)
                params += ';'.join(
                    f"{obj}{f'.{m2}stream' if not m2.isnumeric() else ''}[{index}].{k}={int(v) if isinstance(v, bool) else v}"
                    for k, v in val.items()
                )
                params += ';'
            script = params
        return func(remote, script)

    return wrapper


def comp(t0: tuple, t1: tuple) -> Iterator[bool]:
    """
    Generator function, accepts two tuples.

    Evaluates equality of each member in both tuples.
    """
    for a, b in zip(t0, t1):
        yield a == b


def grouper(n, iterable, fillvalue=None):
    """
    Group elements of an iterable by sets of n length
    """
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def deep_merge(dict1, dict2):
    """Generator function for deep merging two dicts"""
    for k in set(dict1) | set(dict2):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield k, dict(deep_merge(dict1[k], dict2[k]))
            else:
                yield k, dict2[k]
        elif k in dict1:
            yield k, dict1[k]
        else:
            yield k, dict2[k]
