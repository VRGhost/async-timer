import asyncio
import itertools

import async_timer
import asyncstdlib
import pytest


class TestAsyncFunc:
    @pytest.fixture
    def count_fn(self):
        """A function that returns incrementing ints"""
        gen = itertools.count()
        return lambda: next(gen)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("stop_method_name", ["stop", "cancel"])
    async def test_api_call(self, count_fn, stop_method_name):
        vals = []
        timer = async_timer.Timer(10e-5, target=lambda: vals.append(count_fn()))
        timer.start()
        await asyncio.sleep(0.5)
        stop_method = getattr(timer, stop_method_name)
        await stop_method()
        after_cancel_vals = tuple(vals)
        await asyncio.sleep(0.1)
        after_sleep_vals = tuple(vals)

        assert len(vals) > 10, len(vals)
        assert tuple(vals) == after_cancel_vals
        assert tuple(vals) == after_sleep_vals

    @pytest.mark.asyncio
    async def test_join_non_running_timer(self, count_fn):
        timer = async_timer.Timer(10e-5, target=lambda: count_fn())
        with pytest.raises(asyncio.CancelledError):
            await timer.join()

    @pytest.mark.asyncio
    async def test_async_ctx_call(self, count_fn):
        vals = []
        async with async_timer.Timer(10e-5, target=lambda: vals.append(count_fn())):
            await asyncio.sleep(0.1)
        after_ctx_vals = tuple(vals)
        await asyncio.sleep(0.1)
        after_sleep_vals = tuple(vals)

        assert len(vals) > 10, len(vals)
        assert tuple(vals) == after_ctx_vals
        assert tuple(vals) == after_sleep_vals

    @pytest.mark.asyncio
    async def test_dual_start(self, count_fn):
        vals = []
        async with async_timer.Timer(
            10e-5, target=lambda: vals.append(count_fn())
        ) as timer:
            with pytest.raises(RuntimeError):
                timer.start()
            assert timer.is_running()
        assert not timer.is_running()

    @pytest.mark.asyncio
    async def test_timer_subscribe_async_fn(self, count_fn):
        vals = []
        async_for_vals = []

        async def _target():
            val = count_fn()
            await asyncio.sleep(10e-7)
            vals.append(val)
            return val

        async with async_timer.Timer(10e-5, target=_target) as timer:
            async for (idx, val) in asyncstdlib.enumerate(timer):
                async_for_vals.append(val)
                await asyncio.sleep(0.01)
                if idx > 11:
                    break

        assert len(vals) > 10
        assert len(async_for_vals) > 10
        assert set(async_for_vals).issubset(vals)

    @pytest.mark.asyncio
    async def test_timer_subscribe_sync_fn(self, count_fn):
        vals = []
        async_for_vals = []

        def _target():
            val = count_fn()
            vals.append(val)
            return val

        async with async_timer.Timer(10e-5, target=_target) as timer:
            async for (idx, val) in asyncstdlib.enumerate(timer):
                async_for_vals.append(val)
                await asyncio.sleep(0.01)
                if idx > 11:
                    break

        assert len(vals) > 10
        assert len(async_for_vals) > 10
        assert set(async_for_vals).issubset(vals)

    @pytest.mark.asyncio
    async def test_timer_subscribe_sync_generator(self, count_fn):
        vals = []
        async_for_vals = []

        def _target():
            while True:
                el = count_fn
                vals.append(el)
                yield el

        async with async_timer.Timer(10e-5, target=_target) as timer:
            async for (idx, val) in asyncstdlib.enumerate(timer):
                async_for_vals.append(val)
                await asyncio.sleep(0.01)
                if idx > 11:
                    break

        assert len(vals) > 10
        assert len(async_for_vals) > 10
        assert set(async_for_vals).issubset(vals)

    @pytest.mark.asyncio
    async def test_timer_subscribe_async_generator(self, count_fn):
        vals = []
        async_for_vals = []

        async def _target():
            while True:
                el = count_fn
                vals.append(el)
                yield el
                await asyncio.sleep(10e-4)

        async with async_timer.Timer(10e-5, target=_target) as timer:
            async for (idx, val) in asyncstdlib.enumerate(timer):
                async_for_vals.append(val)
                await asyncio.sleep(0.01)
                if idx > 11:
                    break

        assert len(vals) > 10
        assert len(async_for_vals) > 10
        assert set(async_for_vals).issubset(vals)

    @pytest.mark.asyncio
    async def test_timer_exception(self):
        vals = []

        def _target():
            for idx in itertools.count():
                vals.append(idx)
                yield idx
                if idx > 10:
                    raise NameError("Something went wrong")

        iter_vals = []
        async with async_timer.Timer(10e-5, target=_target) as timer:
            with pytest.raises(NameError) as err:
                async for val in timer:
                    iter_vals.append(val)
                    await asyncio.sleep(10e-10)
            assert "Something went wrong" in str(err)

        assert len(vals) > 10
        assert len(iter_vals) > 10
        assert set(iter_vals).issubset(vals)

    @pytest.mark.asyncio
    async def test_async_generator_exit(self):
        async def _target():
            for idx in itertools.count():
                yield idx
                await asyncio.sleep(10e-10)
                if idx >= 20:
                    break

        iter_vals = []
        async with async_timer.Timer(10e-5, target=_target) as timer:
            async for val in timer:
                iter_vals.append(val)
                await asyncio.sleep(10e-10)

        assert len(iter_vals) == 21

    @pytest.mark.asyncio
    async def test_sync_generator_exit(self):
        def _target():
            for idx in itertools.count():
                yield idx
                if idx >= 20:
                    break

        iter_vals = []
        async with async_timer.Timer(10e-5, target=_target) as timer:
            async for val in timer:
                iter_vals.append(val)
                await asyncio.sleep(10e-10)

        assert len(iter_vals) == 21
