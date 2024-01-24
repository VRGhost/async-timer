import time

import pytest

from mock_async_timer.timer import MockPacemaker as MockPacemaker


@pytest.mark.asyncio
async def test_no_sleep():
    """Confirm that the mock pacemaker does not sleep."""
    start_time = time.monotonic()
    pm = MockPacemaker(delay=10_000)
    hit_count = 0
    async for _ in pm:
        hit_count += 1
        if hit_count >= 1000:
            break
    end_time = time.monotonic()

    assert hit_count == 1000
    assert (end_time - start_time) < 1, "The mock pacemaker does not sleep."
    assert pm.sleep.await_count == 1000 - 1, "-1 as the first iter does no sleep()"
    pm.sleep.assert_called_with(10_000)


@pytest.mark.asyncio
async def test_stop_via_event():
    """Confirm that the mock pacemaker does not sleep."""
    start_time = time.monotonic()
    pm = MockPacemaker(delay=10_000)
    hit_count = 0
    async for _ in pm:
        hit_count += 1
        if hit_count >= 1000:
            pm._cancel_evt.set()
    end_time = time.monotonic()

    assert hit_count == 1000
    assert (end_time - start_time) < 1, "The mock pacemaker does not sleep."
    assert pm.sleep.await_count == 1000 - 1, "-1 as the first iter does no sleep()"
    pm.sleep.assert_called_with(10_000)
