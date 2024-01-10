# -*- coding: utf-8 -*-
import asyncio
from functools import update_wrapper
from typing import Callable


def coro(f: Callable):
    f = asyncio.coroutine(f)  # type: ignore

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))
    return update_wrapper(wrapper, f)
