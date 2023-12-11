"""Utility async io functions"""
import asyncio
import inspect
import logging
import sys
import typing

logger = logging.getLogger(__name__)
T = typing.TypeVar("T")


class FanoutRv:
    """An object that shares a result actoss all waiters"""

    lock: asyncio.Lock
    futures: typing.List[asyncio.Future]

    def __init__(self):
        self.futures = []
        self.lock = asyncio.Lock()

    async def wait(self):
        """Wait for result to be posted"""
        future = asyncio.get_running_loop().create_future()
        async with self.lock:
            self.futures.append(future)
        return await future

    async def send_result(self, result):
        async with self.lock:
            for future in self.futures:
                future.set_result(result)
            self.futures.clear()

    async def send_exception(self, exc):
        async with self.lock:
            for future in self.futures:
                future.set_exception(exc)
            self.futures.clear()

    async def cancel(self):
        async with self.lock:
            for future in self.futures:
                future.cancel()
            self.futures.clear()


def _default_main_loop_exception_callback(exc_type, exc_val, exc_tb):
    logger.exception("An unexpected exception in the timer loop.")


class Timer:
    delay: float
    target: typing.Callable[[], T]

    result_fanout: FanoutRv
    main_task: typing.Optional[asyncio.Task] = None
    exception_callback: typing.Callable[[typing.Any, typing.Any, typing.Any], None]

    def __init__(
        self,
        delay: float,
        target: typing.Callable[[], T],
        exc_cb: typing.Callable[
            [typing.Any, typing.Any, typing.Any], None
        ] = _default_main_loop_exception_callback,
    ):
        self.delay = delay
        self.target = target
        self.result_fanout = FanoutRv()
        self.exception_callback = exc_cb

    def start(self):
        """Schedule the timer to run."""
        if self.main_task:
            raise RuntimeError("Already running")
        else:
            loop = asyncio.get_running_loop()  # there MUST be a running loop
            self.main_task = loop.create_task(self._loop_callback_routine())

    def is_running(self) -> bool:
        """Return `True` if the timer is currently scheduled"""
        return (self.main_task is not None) and (not self.main_task.done())

    async def __aenter__(self):
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cancel()

    def __aiter__(self):
        return self

    async def join(self):
        """Wait for the next tick of the timer"""
        if not self.is_running():
            raise asyncio.CancelledError("The timer is not running.")
        return (
            await self.result_fanout.wait()
        )  # this can raise `asyncio.CancelledError`

    async def __anext__(self):
        try:
            return await self.join()
        except asyncio.CancelledError as err:
            raise StopAsyncIteration() from err

    def _maybe_detect_generator(
        self, target_rv
    ) -> typing.Tuple[typing.Any, typing.Callable[[], T]]:
        """Check if the value returned by the `self.target` call is a
        kind of generator (sync or async).

        Returns a (this_iter_rv, new_callable) tuple
        """
        if inspect.isgenerator(target_rv):

            def _lock_sync_gen_ctx(gen_src):
                return lambda: next(gen_src)

            get_next_val = _lock_sync_gen_ctx(target_rv)
            rv = (get_next_val(), get_next_val)
        elif inspect.isasyncgen(target_rv):

            def _lock_async_gen_ctx(gen_src):
                return lambda: gen_src.__anext__()

            get_next_val = _lock_async_gen_ctx(target_rv)
            rv = (get_next_val(), get_next_val)
        else:
            rv = (target_rv, None)
        return rv

    async def _loop_callback_routine(self):
        get_next_val = self.target
        first_iter = True
        try:
            while True:
                try:
                    next_val = get_next_val()
                    if first_iter:
                        (next_val, updated_get_next_val) = self._maybe_detect_generator(
                            next_val
                        )
                        if updated_get_next_val is not None:
                            get_next_val = updated_get_next_val
                    if inspect.isawaitable(next_val):
                        rv = await next_val
                    else:
                        rv = next_val
                    if isinstance(rv, (StopIteration, StopAsyncIteration)):
                        break
                except Exception as err:
                    await self.result_fanout.send_exception(err)
                    self.exception_callback(*sys.exc_info())
                    break
                else:
                    await self.result_fanout.send_result(rv)
                first_iter = False
                await asyncio.sleep(self.delay)
        finally:
            # Main loop finished - cancel all watchers
            await self.result_fanout.cancel()

    async def cancel(self):
        """Unshedule the timer"""
        if self.main_task:
            self.main_task.cancel()
            await self.result_fanout.cancel()
            self.main_task = None

    async def stop(self):
        """An alias to `cancel()`"""
        return await self.cancel()
