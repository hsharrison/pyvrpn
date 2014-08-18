import abc
from uuid import uuid4

import vrpn
import pyglet

from pyvrpn.logging import setup_module_logging

error, warning, info, debug = setup_module_logging(__name__)

__all__ = [
    'TestTracker',
    'TestButton',
    'TestDial',
    'PolhemusLibertyLatus',
]


class Receiver(pyglet.event.EventDispatcher, metaclass=abc.ABCMeta):
    """VRPN receiver.

    A |pyglet.event.EventDispatcher| representing one VRPN receiver device.
    A metaclass, it must be subclassed to be used.
    Subclasses should override:
      - |device_type|, the name of the device as recognized by the server config file (e.g. ``'vrpn_Tracker_NULL'``).
      - |object_class|, the class from vrpn.receiver to instantiate the receiver (e.g., ``vrpn.receiver.Tracker``).
      - |n_sensors|, if sensor-specific callbacks are desired (only works for ``vrpn.receiver.Tracker`` devices).
      - |extend_config_line_with_backslash|,
        set to True if additional lines in the config file need to be separated with a backslash.
    Subclasses should also document the required arguments (`config_args`).
    Once instantiated, use |EventDispatcher| methods to set handlers for the ``'on_input'`` event.
    This event fires whenever new data is received from the tracker.
    Handler functions should take a single parameter, taking raw data from the tracker in the form of a dictionary.
    To set sensor-specific callbacks, add handlers to the individual sensors (each also an |EventDispatcher|).
    Individual sensors can be access via indexing the |Receiver| object.

    Parameters
    ----------
    config_args : varies
        The sequence of arguments needed to define this device in the server configuration file.
        See the sample ``vrpn.cfg`` to determine these arguments.
    additional_config_lines : list of str, optional
        Additional lines to write to the configuration file.
        For example, commands to send to the device.

    Attributes
    ----------
    config_args : varies
    additional_config_lines : list of str
    name : str
        A uniquely identifying name, generated randomly.
    connected : bool
        True if the Receiver has already been connected to a server.
    device_type : str
        The name of the device as recognized by the server configuration file.
    object_class : type
        The class from ``vrpn.receiver`` to instantiate the device.
    config_text : str
        The server configuration file entry for this device.
    callback_type : str
    n_sensors : int

    """
    extend_config_line_with_backslash = False

    def __init__(self, *config_args, additional_config_lines=None):
        self.config_args = config_args
        self.additional_config_lines = additional_config_lines or []
        self.name = uuid4().hex
        self._object = None
        self.is_connected = False

        self._sensors = [Sensor(str(self), ix) for ix in range(self.n_sensors)]

    @abc.abstractproperty
    def device_type(self):
        """Subclasses should override using a class attribute."""
        pass

    @abc.abstractproperty
    def object_class(self):
        """Subclasses should override using a class attribute."""
        pass

    @property
    def n_sensors(self):
        """
        Used only by |vrpn.receiver.Tracker| receivers.
        Can be provided by subclasses.
        If specified, event handlers will be created for individual sensors (|Sensor| objects),
        *in addition to* an event handler for the entire tracker (this |Receiver| object).

        """
        return 0

    @property
    def callback_type(self):
        """
        A required parameter for ``vrpn.receiver.Tracker.register_change_handler``.
        Valid options are ``{'position', 'velocity', 'acceleration', 'workspace', 'unit2sensor', 'tracker2room'}``.
        From limited testing (only with Polhemus Liberty Latus),
        if ``'position'`` is used all tracker data is received.

        """
        if self.object_class is vrpn.receiver.Tracker:
            return 'position'

    @property
    def config_text(self):
        first_line_items = [self.device_type, self.name]
        first_line_items.extend(str(arg) for arg in self.config_args)

        lines = ['\t'.join(first_line_items)]
        lines.extend(self.additional_config_lines)

        joiner = '\\\n' if self.extend_config_line_with_backslash else '\n'
        return joiner.join(lines) + '\n'

    def connect(self, host='localhost'):
        """
        Connect this device to a running server.

        Parameters
        ----------
        host : str, optional
            IP address of server.
            Defaults to ``'localhost'``.

        """
        if self.is_connected:
            raise RuntimeError('cannot connect a Receiver twice')

        self._object = self.object_class('{}@{}'.format(self.name, host))

        if self.callback_type:
            # First option to register_change_handler is user_data, which we don't use.
            self._object.register_change_handler('', self._callback, self.callback_type)
            # A sensor can be specified only if callback_type is also specified.
            for ix, sensor in enumerate(self._sensors):
                self._object.register_change_handler('', sensor._callback, self.callback_type, ix)

        else:
            self._object.register_change_handler('', self._callback)

        info('{} connected to server'.format(self))
        self.is_connected = True

    def mainloop(self):
        """Call this method regularly to ensure that data is received promptly."""
        self._object.mainloop()

    def _callback(self, user_data, data):
        self.dispatch_event('on_input', data)
        debug('dispatched on_input event for {}'.format(self))
        # Manually dispatch sensor events for non-trackers.
        if self.n_sensors:
            if 'button' in data:
                self[data['button']].dispatch_event('on_input', data)
                debug('dispatched on_input event for {}'.format(self[data['button']]))
            elif 'dial' in data:
                self[data['dial']].dispatch_event('on_input', data)
                debug('dispatched on_input event for {}'.format(self[data['dial']]))

    def __str__(self):
        return '{} {} ({})'.format(self.device_type, self.name, type(self).__name__)

    def __bool__(self):
        return True

    def __getitem__(self, item):
        return self._sensors.__getitem__(item)

    def __len__(self):
        return self.n_sensors

    def __iter__(self):
        return iter(self._sensors)

    def __reversed__(self):
        return reversed(self._sensors)


class Sensor(pyglet.event.EventDispatcher):
    """VRPN sensor.

    A |pyglet.event.EventDispatcher| associated with an individual sensor of a tracker.
    Use |EventDispatcher| methods to register handlers for the ``'on_input'`` event.
    These handlers should take a single argument, raw data from the tracker as a dictionary.

    Sensors should not be directly instantiated, they will be automatically created by the parent |Receiver|.

    Attributes
    ----------
    number : int
        The number of the associated sensor.

    """
    def __init__(self, parent_str, number):
        self._parent_str = parent_str
        self.number = number

    def _callback(self, user_data, data):
        self.dispatch_event('on_input', data)
        debug('dispatched on_input event for {}'.format(self))

    def __str__(self):
        return 'Sensor #{} of {}'.format(self.number, self._parent_str)

    def __bool__(self):
        return True


class FirstArgumentIsNSensors(Receiver):
    """
    A mixin class to use when the first config argument specifies the number of sensors/buttons/dials.

    """
    @property
    def n_sensors(self):
        return self.config_args[0]


class Tracker(Receiver):
    """Tracker receivers can derive from this instead of |Receiver|, and then don't have to override |object_class|.

    """
    object_class = vrpn.receiver.Tracker


class Dial(Receiver):
    """Dial receivers can derive from this instead of |Receiver|, and then don't have to override |object_class|."""
    object_class = vrpn.receiver.Dial


class Button(Receiver):
    """Button receivers can derive from this instead of |Receiver|, and then don't have to override |object_class|."""
    object_class = vrpn.receiver.Button


class Analog(Receiver):
    """Analog receivers can derive from this instead of |Receiver|, and then don't have to override |object_class|."""
    object_class = vrpn.receiver.Analog


class Text(Receiver):
    """Text receivers can derive from this instead of |Receiver|, and then don't have to override |object_class|."""
    object_class = vrpn.receiver.Text


class TestTracker(Tracker, FirstArgumentIsNSensors):
    """
    Reports identity information for each of its sensors at a specified rate.

    Parameters
    ----------
    n_sensors : int
        Number of sensors to report.
    rate_at_which_to_report_updates : float
        Rate, in Hz, at which data is reported.

    """
    device_type = 'vrpn_Tracker_NULL'


class TestButton(Button, FirstArgumentIsNSensors):
    """
    Reports on and off events for each of its buttons at a specified rate.

    Parameters
    ----------
    n_buttons : int
        Number of buttons to report.
    rate_at_which_buttons_toggle : float
        Rate, in Hz, at which data is reported.

    """
    device_type = 'vrpn_Button_Example'


class TestDial(Dial, FirstArgumentIsNSensors):
    """
    Reports constant rotations for each of its dials at the specified rate.

    Parameters
    ----------
    n_dials : int
        Number of dials to report
    rate_at_which_dials_spin : float
        Rate to spin the dials, in revolutions per second.
    rate_at_which_to_report_updates : float
        Rate, in Hz, at which data is reported.

    """
    device_type = 'vrpn_Dial_Example'


class PolhemusLibertyLatus(Tracker, FirstArgumentIsNSensors):
    """Polhemus Liberty Latus high-speed tracker.

    Parameters
    ----------
    n_markers : int
        Number of markers (sensors) to launch.
    additional_config_lines : list of str, optional
        Additional lines to write to the config file (commands to send to the Polhemus).

    """
    device_type = 'vrpn_Tracker_LibertyHS'
    extend_config_line_with_backslash = True

    def __init__(self, n_markers, additional_config_lines=None):
        # Second argument is baudrate, which has no effect; 115200 is a sensible value.
        super().__init__(n_markers, 115200, additional_config_lines=additional_config_lines)


Receiver.register_event_type('on_input')
Sensor.register_event_type('on_input')
