import pytest

import mock_async_timer


def test_import():
    hasattr(mock_async_timer, "MockTimer")


@pytest.mark.asyncio
async def test_join_works():
    hit_count = 0

    def _target():
        nonlocal hit_count
        hit_count += 1
        if hit_count >= 1000:
            raise StopIteration

    mock_timer = mock_async_timer.MockTimer(target=_target, delay=10_000, start=True)

    assert mock_timer.is_running()
    await mock_timer.wait(), "Wait for it to exit"

    assert hit_count == 1000
    assert not mock_timer.is_running()
    assert mock_timer.delay == 10_000
    assert mock_timer.pacemaker.sleep.await_count == 999
