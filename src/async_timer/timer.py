"""Utility async io functions"""
import asyncio
import inspect
import typing

T = typing.TypeVar("T")


class FanoutRv:
    """An object that shares a result actoss all waiters"""

    lock: asyncio.Lock
    futures: list[asyncio.Future]

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
                future.cancel("Ther timer is shutting down")
            self.futures.clear()


class Timer:
    delay: float
    target: typing.Callable[[], T]

    result_fanout: FanoutRv
    main_task: asyncio.Task | None = None

    def __init__(self, delay: float, target: typing.Callable[[], T]):
        self.delay = delay
        self.target = target
        self.result_fanout = FanoutRv()

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
        return await self.result_fanout.wait()  # this can raise `asyncio.CancelledError`

    async def __anext__(self):
        try:
            return await self.join()
        except asyncio.CancelledError as err:
            raise StopAsyncIteration() from err

    async def _loop_callback_routine(self):
        get_next_val = self.target
        first_iter = True
        try:
            while True:
                try:
                    maybe_coro = get_next_val()
                    if first_iter:  # noqa
                        # Adjust the `get_next_val` on the actual
                        # return value of the `self.target`
                        if inspect.isgenerator(maybe_coro):

                            def _lock_sync_gen_ctx(gen_src=maybe_coro):
                                return lambda: next(gen_src)

                            get_next_val = _lock_sync_gen_ctx()
                            maybe_coro = get_next_val()
                        elif inspect.isasyncgen(maybe_coro):

                            def _lock_async_gen_ctx(gen_src=maybe_coro):
                                return lambda: anext(gen_src)

                            get_next_val = _lock_async_gen_ctx()
                            maybe_coro = get_next_val()
                    if inspect.isawaitable(maybe_coro):
                        rv = await maybe_coro
                    else:
                        rv = maybe_coro
                    if isinstance(rv, (StopIteration, StopAsyncIteration)):
                        break
                except Exception as err:
                    await self.result_fanout.send_exception(err)
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
