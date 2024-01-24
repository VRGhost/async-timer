"""Test the async cancel feature"""

import asyncio
import itertools

import pytest
import pytest_asyncio

import async_timer


@pytest.fixture
def timer_rv():
    return []


@pytest.fixture
def count_fn():
    """A function that returns incrementing ints"""
    gen = itertools.count()
    return lambda: next(gen)


@pytest_asyncio.fixture
async def cancel_fut_1():
    return asyncio.Future()


@pytest_asyncio.fixture
async def cancel_fut_2():
    return asyncio.Future()


@pytest_asyncio.fixture
async def timer(timer_rv, count_fn, cancel_fut_1, cancel_fut_2):
    return async_timer.Timer(
        delay=10_000,
        target=lambda: timer_rv.append(count_fn()),
        cancel_aws=[cancel_fut_1, cancel_fut_2],
        start=True,
    )


@pytest.mark.asyncio
async def test_fut1_fire(cancel_fut_1, timer):
    async def fire_fut():
        await asyncio.sleep(0.2)
        cancel_fut_1.set_result(42)
        return "hey there"

    (fire_fut_rv, timer_rv) = await asyncio.gather(
        fire_fut(), timer.wait(), return_exceptions=True
    )
    assert fire_fut_rv == "hey there"
    assert timer_rv is None
