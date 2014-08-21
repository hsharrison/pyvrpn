import logging
from unittest.mock import MagicMock

import pytest
import vrpn

from pyvrpn import receiver


# Set up logging to file in case something hangs and we have to Ctrl-C.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-15s %(lineno)-4s %(levelname)-6s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='test_receiver.log',
                    filemode='w')


def test_object_classes():
    assert receiver.TestTracker.object_class is vrpn.receiver.Tracker
    assert receiver.TestButton.object_class is vrpn.receiver.Button
    assert receiver.TestDial.object_class is vrpn.receiver.Dial
    assert receiver.PolhemusLibertyLatus.object_class is vrpn.receiver.Tracker


def test_device_type():
    assert receiver.TestTracker.device_type == 'vrpn_Tracker_NULL'
    assert receiver.TestButton.device_type == 'vrpn_Button_Example'
    assert receiver.TestDial.device_type == 'vrpn_Dial_Example'
    assert receiver.PolhemusLibertyLatus.device_type == 'vrpn_Tracker_LibertyHS'


def test_event_types():
    assert receiver.Receiver.event_types == ['on_input']
    assert receiver.Sensor.event_types == ['on_input']


def test_callback_type():
    assert receiver.TestTracker(1, 1).callback_type == receiver.PolhemusLibertyLatus(1).callback_type == 'position'
    assert receiver.TestButton(1, 1).callback_type is None


def test_sensors():
    tracker = receiver.TestTracker(2, 1)
    assert tracker
    assert tracker[0]
    assert tracker[1]
    assert tracker.n_sensors == len(tracker) == tracker.config_args[0] == 2
    assert isinstance(tracker[0], receiver.Sensor)
    assert isinstance(tracker[1], receiver.Sensor)
    button = receiver.TestButton(2, 1)
    assert button.n_sensors == len(button) == button.config_args[0] == 2
    assert isinstance(button[0], receiver.Sensor)
    assert isinstance(button[1], receiver.Sensor)
    dial = receiver.TestDial(2, 1, 1)
    assert dial.n_sensors == len(dial) == dial.config_args[0] == 2
    assert isinstance(dial[0], receiver.Sensor)
    assert isinstance(dial[1], receiver.Sensor)
    tracker = receiver.PolhemusLibertyLatus(2)
    assert tracker.n_sensors == len(tracker) == tracker.config_args[0] == 2
    assert isinstance(tracker[0], receiver.Sensor)
    assert isinstance(tracker[1], receiver.Sensor)
    assert list(tracker) == [tracker[0], tracker[1]]
    assert list(reversed(tracker)) == [tracker[1], tracker[0]]


def test_config_text():
    tracker = receiver.TestTracker(1, 1.0)
    config_fields = tracker.config_text.split()
    assert config_fields[0] == 'vrpn_Tracker_NULL'
    assert config_fields[1] == tracker.uuid
    assert config_fields[2] == '1'
    assert config_fields[3] == '1.0'


def test_connect():
    button = receiver.TestButton(2, 1.0)
    assert not button.is_connected
    button.object_class = MagicMock()
    button.connect()
    assert button.is_connected
    assert button.object_class.called_with('{}@localhost'.format(button.uuid))
    assert button._object.register_change_handler.called_with('', button._callback)

    tracker = receiver.TestTracker(2, 1.0)
    assert not tracker.is_connected
    tracker.object_class = MagicMock()
    tracker.connect()
    assert tracker.is_connected
    assert tracker.object_class.called_with('{}@localhost'.format(tracker.uuid))
    assert tracker._object.register_change_handler.called_with(
        '', tracker[-1]._callback, 'position', len(tracker)
    )
    with pytest.raises(RuntimeError):
        tracker.connect()

