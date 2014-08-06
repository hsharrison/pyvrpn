import asyncio
import functools
import logging
from datetime import datetime

import pytest

try:
    import cytoolz as toolz
except ImportError:
    import toolz

from pyvrpn.server import monitor_feed, Server, decoded_readline


# Set up logging to file in case something hangs and we have to Ctrl-C.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-13s %(lineno)-4s %(levelname)-6s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='test.log',
                    filemode='w')


@pytest.fixture
def loop():
    return asyncio.get_event_loop()


def async_test(func):
    @functools.wraps(func)
    def wrapper(loop, *args, **kwargs):
        coro = asyncio.coroutine(func)
        loop.run_until_complete(coro(loop, *args, **kwargs))
    return wrapper


@toolz.curry
def appender(list_, item, stop_at='0'):
    item = item[:-1]
    if item == stop_at:
        raise StopIteration
    list_.append(item)


@async_test
def test_monitor_stream_end_process(loop):
    items = []
    with open('tests/test_data.txt', 'rb') as file:
        yield from monitor_feed((appender(items, stop_at='3')), decoded_readline(file))
    assert items == [str(i) for i in range(3)]


@async_test
def test_monitor_stream_end_stream(loop):
    items = []
    with open('tests/test_data.txt', 'rb') as file:
        yield from monitor_feed((appender(items, stop_at='30')), decoded_readline(file))
    assert items == [str(i) for i in range(10)]


def test_bad_with_statement():
    with pytest.raises(RuntimeError):
        with Server([], loop=loop) as server:
            pass


@async_test
def test_bad_start_server(loop):
    server = Server([], loop=loop)
    yield from server.start()
    with pytest.raises(RuntimeError):
        yield from server.start()
    # Still have to stop it.
    yield from server.stop()


@async_test
def test_server_basic_call(loop):
    server = Server([], loop=loop, _exe=['tests/dummy_server.py', '-f'])
    assert not server.is_running
    yield from server.start()
    assert server.is_running
    yield from server.stop()
    assert not server.is_running


@async_test
def test_server_process_noop(loop):
    """Make sure the server exits after the with statement."""
    with (yield from Server([], loop=loop)) as server:
        assert server.is_running
    yield from asyncio.sleep(0.05)
    assert not server.is_running


@async_test
def test_server_process_dummy(loop):
    """Make sure the server exits after the with statement."""
    with (yield from Server([], loop=loop, _exe=['tests/dummy_server.py', '-f'])) as server:
        assert server.is_running
    yield from asyncio.sleep(0.05)
    assert not server.is_running


@async_test
def test_server_too_fast(loop):
    with pytest.raises(RuntimeError):
        with (yield from Server([], loop=loop, _exe=['cat'])) as server:
            pass



@async_test
def test_server_process_exception(loop):
    """Make sure the server exits after an exception."""
    try:
        with (yield from Server([], loop=loop, _exe=['tests/dummy_server.py', '-f'])) as server:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
    finally:
        yield from asyncio.sleep(0.05)
        assert not server.is_running


@asyncio.coroutine
def startup_time(*args, loop=None, **kwargs):
    server = Server(*args, loop=loop, **kwargs)
    started_at = datetime.now()
    yield from asyncio.wait_for(server.start(), None, loop=loop)
    return server, (datetime.now() - started_at).total_seconds()


@async_test
def test_startup_time(loop):
    server, time = yield from startup_time([], loop=loop)
    assert server.is_running
    assert time < 0.5
    yield from server.stop()
    assert not server.is_running


@async_test
def test_server_sentinel(loop):
    server, time = yield from startup_time(
        ['sentinel\n'],
        sentinel='sentinel',
        loop=loop,
        _exe=['tests/dummy_server.py', '-r', '2', '-f']
    )
    assert server.is_running
    assert 0.5 < time < 1
    yield from server.stop()
    assert not server.is_running

    server, time = yield from startup_time(
        ['a\n', 'b\n', 'c\n', 'd\n', 'e\n', 'sentinel\n'],
        sentinel='sentinel',
        loop=loop,
        _exe=['tests/dummy_server.py', '-r', '2', '-f']
    )
    assert server.is_running
    assert 1 < time < 1.5
    yield from asyncio.sleep(.2, loop=loop)
    assert 0.1 < server.time < 0.3
    yield from server.stop()
    assert not server.is_running


@async_test
def test_bad_server_stop(loop):
    server = Server([], loop=loop)
    with pytest.raises(RuntimeError):
        yield from server.stop()
