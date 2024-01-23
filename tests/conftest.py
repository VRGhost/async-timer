import asyncio
import itertools

import pytest
import pytest_asyncio


@pytest.fixture
def count_iterable():
    """Sync iterable that returning incrementing ints"""
    return itertools.count


@pytest.fixture
def count_gen(count_iterable):
    def _generator():
        for val in count_iterable():
            yield val

    return _generator


@pytest.fixture
def count_fn(count_gen):
    """A sync function that returns incrementing ints"""
    gen = count_gen()
    return lambda: next(gen)


@pytest_asyncio.fixture
async def async_count_fn():
    """A sync function that returns incrementing ints"""
    gen = itertools.count()

    async def _get_next():
        await asyncio.sleep(10e-5)
        return next(gen)

    return _get_next


@pytest_asyncio.fixture
async def async_gen(count_iterable):
    """A sync function that returns incrementing ints"""

    async def _iter():
        for val in count_iterable():
            await asyncio.sleep(10e-5)
            yield val

    return _iter
