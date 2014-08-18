import asyncio
import functools
from collections import Counter
import logging

import pytest

try:
    import cytoolz as toolz
except ImportError:
    import toolz

from pyvrpn import receiver, server


# Set up logging to file in case something hangs and we have to Ctrl-C.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-13s %(lineno)-4s %(levelname)-6s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='test_receiver.log',
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
def count(data_store, key, data):
    data_store[key] += 1


@async_test
def test_test_devices(loop):
    tracker = receiver.TestTracker(2, 1)
    assert len(tracker) == 2
    button = receiver.TestButton(2, 2)
    dial = receiver.TestDial(2, 1, 2)
    counts = Counter()
    devices = [tracker, button, dial]
    for device, key in zip(devices, ['tracker', 'button', 'dial']):
        device.set_handler('on_input', count(counts, key))
    tracker[0].set_handler('on_input', count(counts, 'tracker[0]'))
    tracker[1].set_handler('on_input', count(counts, 'tracker[1]'))
    button[0].set_handler('on_input', count(counts, 'button[0]'))
    button[1].set_handler('on_input', count(counts, 'button[1]'))
    dial[0].set_handler('on_input', count(counts, 'dial[0]'))
    dial[1].set_handler('on_input', count(counts, 'dial[1]'))
    with (yield from server.LocalServer(devices)):
        yield from asyncio.sleep(1)
    assert counts['tracker[0]'] in (1, 2)
    assert counts['tracker[1]'] in (1, 2)
    assert counts['tracker'] == counts['tracker[0]'] + counts['tracker[1]']
    assert counts['button[0]'] in (1, 2)
    assert counts['button[1]'] in (1, 2)
    assert counts['button'] == counts['button[0]'] + counts['button[1]']
    assert counts['dial[0]'] in (1, 2)
    assert counts['dial[1]'] in (1, 2)
    assert counts['dial'] == counts['dial[0]'] + counts['dial[1]']


@async_test
def test_connect_twice(loop):
    tracker = receiver.TestTracker(1, 1)
    with (yield from server.LocalServer([tracker])):
        with pytest.raises(RuntimeError):
            tracker.connect()
