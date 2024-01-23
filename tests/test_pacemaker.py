import asyncio
import time

import pytest

import async_timer.pacemaker as pacemaker


@pytest.mark.asyncio
async def test_simple():
    pm = pacemaker.TimerPacemaker(delay=10e-5)
    test_time = 0.5
    start_time = time.monotonic()
    iter_count = 0

    async for _ in pm:
        iter_count += 1
        if (time.monotonic() - start_time) > test_time:
            break
    assert iter_count > 100


@pytest.mark.asyncio
async def test_cancel():
    pm = pacemaker.TimerPacemaker(delay=10e-5)
    iter_count = 0

    async for _ in pm:
        iter_count += 1
        if iter_count == 100:
            pm.stop()
    assert iter_count == 100, "no further iterations happened"


@pytest.mark.asyncio
async def test_cancel_by_fut_result():
    cancel_fut = asyncio.Future()
    pm = pacemaker.TimerPacemaker(delay=10e-5)
    pm.stop_on([cancel_fut])
    iter_count = 0

    async for _ in pm:
        iter_count += 1
        if iter_count == 100:
            cancel_fut.set_result(42)
    assert iter_count == 100, "no further iterations happened"


@pytest.mark.asyncio
async def test_cancel_by_fut_exc():
    cancel_fut = asyncio.Future()
    pm = pacemaker.TimerPacemaker(delay=10e-5)
    pm.stop_on([cancel_fut])
    iter_count = 0

    async for _ in pm:
        iter_count += 1
        if iter_count == 100:
            cancel_fut.set_exception(Exception("Something happened."))
    assert iter_count == 100, "no further iterations happened"


@pytest.mark.asyncio
async def test_iter_after_stop():
    pm = pacemaker.TimerPacemaker(delay=10e-5)
    pm.stop()

    rvs1 = []
    async for _ in pm:
        rvs1.append(42)

    rvs2 = []
    async for _ in pm:
        rvs2.append(42)

    assert rvs1 == []
    assert rvs2 == []
