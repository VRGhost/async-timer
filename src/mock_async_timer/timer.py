import unittest.mock

import async_timer


class MockPacemaker(async_timer.pacemaker.TimerPacemaker):
    sleep: unittest.mock.AsyncMock

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sleep = unittest.mock.AsyncMock(name="mock-timer-sleep")

    async def _try_wait(self, delay: float):
        if self._cancel_evt.is_set():
            raise StopAsyncIteration()
        await self.sleep(delay)


class MockTimer(async_timer.Timer):
    """Test-friendly mock timer class.

    The main difference is that it is using test-friendly pacemaker
        that doesn't sleep.
    """

    pacemaker: MockPacemaker

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pacemaker = MockPacemaker(self.pacemaker.delay)
