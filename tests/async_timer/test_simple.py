import pytest


def test_import():
    import async_timer

    assert hasattr(async_timer, "Timer")


def test_start_without_async_loop():
    import async_timer

    timer = async_timer.Timer(delay=1, target=lambda: 42)

    with pytest.raises(RuntimeError):
        timer.start()
