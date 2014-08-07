from subprocess import PIPE
import re
from functools import partial
from tempfile import NamedTemporaryFile
import logging
import asyncio
import inspect
import traceback
from datetime import datetime

try:
    import cytoolz as toolz
except ImportError:
    import toolz


SERVER_CMD_ARGS = ['vrpn_server', '-f']


# Set up logging.
_old_factory = logging.getLogRecordFactory()


def _redirect_log_call_record_factory(*args, **kwargs):
    # Because we're logging from a custom function,
    # we should make the line numbers point to the call from the next frame in the stack.
    record = _old_factory(*args, **kwargs)
    frames = inspect.stack()
    stack_no = next(i for i, frame in enumerate(frames) if frame[2] == record.lineno)
    if frames[stack_no][3] == '_log_rstrip':
        record.lineno = frames[stack_no + 1][2]
    return record

logging.setLogRecordFactory(_redirect_log_call_record_factory)
module_logger = logging.getLogger(__name__)


@toolz.curry
def _log_rstrip(logger, level, line):
    logger.log(level, str(line).rstrip())

log = _log_rstrip(module_logger)
debug = log(logging.DEBUG)
info = log(logging.INFO)
error = log(logging.ERROR)


def _iscoroutinefunction(func):
    # Workaround for curried and partial functions.
    if asyncio.iscoroutinefunction(func):
        return True

    return asyncio.iscoroutinefunction(getattr(func, 'func', None))


class Server:
    """Asynchronous wrapper for VRPN server process.

    It's important to always stop the server.
    To that end, it can be used as a coroutine context manager::

        with (yield from pyvrpn.Server(devices_text, sentinel='ready')) as server:
                ...
                ...

    or make sure it closes the old-fashioned way::

        server = pyvrpn.Server(devices_text, sentinel='ready')
        yield from server.start()

        try:
            ...
            ...

        finally:
            yield from server.stop()

    As long as the server process is running,
    the process's stdout will be logged at the INFO level,
    and stderr will be logged at the ERROR level.

    Parameters
    ---------
    device_config__text : iterable of str
        Lines to write to the server config file.
        Usually, each line corresponds to one device.
    server_args : iterable of str, optional
        Command-line arguments to pass to ``vrpn_server`` executable.
    sentinel : str, optional
        A regular expression pattern to look for in the server's stdout.
        The server will not be considered initialized until this pattern is encountered.
    sleep : int, optional
        The number of seconds to wait before the server is considered initialized.
        Sleeping will occur after `sentinel` is found if both options are used.
    loop : |asyncio.EventLoop|, optional
        The event loop to schedule tasks with.

    Attributes
    ----------
    device_config_text : iterable
    server_args : sequence
    sentinel : str
    sleep : int
    loop : |asyncio.EventLoop|
    proc : |asyncio.subprocess.Process|
        The process running the ``vrpn_server`` executable.
    started_at : |datetime.datetime|
        The time when the server completed initialization.
    monitor_tasks : dict of str to |asyncio.Task|
        Contains two tasks, one that monitors the stdout of `proc` and one that monitors its stderr.
    is_running : bool
        Returns True if the server is running.
    time : float
        Number of seconds since `started_at`.

    Notes
    -----

    Due to limits of |asyncio| that are nicely summarized `here`_,
    the ``__exit__`` method (i.e. the stopping of the server at the end of the ``with`` block) cannot block.
    This means that the server process  will still be running
    for another fraction of a second after the ``with`` statement closes.
    For most use cases, this should not matter.

    .. _here: http://python-notes.curiousefficiency.org/en/latest/pep_ideas/async_programming.html#asynchronous-context-managers

    """
    def __init__(self, devices_config_text, server_args=None, sentinel=None, timeout=None, sleep=0, loop=None, _exe=None):
        self.devices_config_text = devices_config_text
        self.server_args = server_args
        self.sentinel = sentinel
        self.timeout = timeout
        self.sleep = sleep
        self.loop = loop
        self._exe = _exe or SERVER_CMD_ARGS

        self.process = None
        self.started_at = None
        self.monitor_tasks = {
            'stdout': None,
            'stderr': None,
        }

    @property
    def is_running(self):
        return self.process.returncode is None if self.process else False

    @property
    def time(self):
        if self.is_running:
            return (datetime.now() - self.started_at).total_seconds()

    @asyncio.coroutine
    def start(self):
        """Start the server asynchronously.

        |Server.start| returns after
        (1) the |sentinel| attribute (if given) is matched in the server's stdout, followed by
        (2) a number of seconds given by the |sleep| attribute.

        This method is a |coroutine|.

        """
        # Don't run multiple servers from the same instance.
        if self.is_running:
            raise RuntimeError("Cannot start a Server that's already is_running")

        with NamedTemporaryFile('w') as config_file:
            config_file.writelines([
                '# VRPN server configuration file.\n',
                '# Automatically created by pyvrpn.server.Server.\n',
                '# If this still exists after the server has stopped,\n',
                '# something went wrong!\n',
            ])
            config_file.writelines(self.devices_config_text)
            config_file.flush()

            # Log the entire contents of the file.
            info('Temporary config file created at {} with contents:'.format(config_file.name))
            with open(config_file.name, 'r') as temp_file:
                for n, line in enumerate(temp_file):
                    info('{}:{:02}:{}'.format(config_file.name, n + 1, line))

            cmd_args = self._exe + [config_file.name]
            if self.server_args:
                cmd_args.extend(self.server_args)

            debug('yielding from coroutine asyncio.create_subprocess_exec')
            self.process = yield from asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=PIPE,
                stderr=PIPE,
                loop=self.loop
            )
            info('Started server process with PID {}.'.format(self.process.pid))

            try:
                debug('running coroutine monitor_feed with asyncio.async')
                self.monitor_tasks['stderr'] = asyncio.async(
                    monitor_feed(
                        error,
                        decoded_readline(self.process.stderr)),
                    loop=self.loop)

                if self.sentinel:
                    debug('yielding from coroutine asyncio.wait_for(monitor_feed())')
                    yield from asyncio.wait_for(
                        monitor_feed(
                            _check_for_pattern(re.compile(self.sentinel), log_func=info),
                            decoded_readline(self.process.stdout)),
                        self.timeout, loop=self.loop
                    )
                debug('running coroutine monitor_feed with asyncio.async')
                self.monitor_tasks['stdout'] = asyncio.async(
                    monitor_feed(
                        info,
                        decoded_readline(self.process.stdout)),
                    loop=self.loop
                )
                debug('yielding from coroutine asyncio.sleep')
                yield from asyncio.sleep(self.sleep, loop=self.loop)

                # Done initialization, make sure sever process is still is_running.
                if self.process.returncode is not None:
                    raise RuntimeError(
                        'Server process exited with exit code {} before initialization completed.'.format(
                            self.process.returncode))

                info('Server initialization completed.')
                self.started_at = datetime.now()

            except:
                self.stop(kill=True)
                raise

    @asyncio.coroutine
    def stop(self, exc_type=None, exc_value=None, exc_tb=None, kill=False):
        """Stop the server asynchronously.

        The monitoring tasks stored in |Server.monitor_tasks| will be canceled,
        then a SIGTERM or SIGKILL signal will be sent to the server process.

        The first three inputs are the same as used for a context manager's |__exit__| method,
        and provide information about an exception.
        If the server is being stopped due to an exception,
        information about the exception can be passed in and it will be logged before killing the process.

        This method is a |coroutine|.

        Parameters
        ----------
        exc_type : type, optional
            The exception type, if the server is being stopped due to an exception.
        exc_value : str, optional
            The value passed to the exception.
        exc_tb : |traceback|, optional
            The exception traceback.
        kill : bool, optional
            If True, send SIGKILL instead of SIGTERM.

        Returns
        -------
        int
            The exit code of the process.

        """
        if not self.is_running:
            raise RuntimeError("Cannot stop a Server that isn't is_running")

        if exc_type is None:
            self.cancel_monitoring()
            if kill:
                self.process.kill()
            else:
                self.process.terminate()
            info('{} sent to server process.'.format('SIGKILL' if kill else 'SIGTERM'))

            debug('yielding from coroutine Server.process.wait')
            exitcode = yield from self.process.wait()
            debug('exit code: {}'.format(exitcode))
            return exitcode

        else:
            info('{}: {}'.format(exc_type.__name__, exc_value))
            for tb in traceback.format_tb(exc_tb):
                info(tb)
            debug('yielding from coroutine Server.stop')
            yield from self.stop(kill=True)

    def cancel_monitoring(self, stream=None):
        if stream:
            debug('canceling Task monitoring {}'.format(stream))
            self.monitor_tasks[stream].cancel()
        else:
            for stream in self.monitor_tasks.keys():
                self.cancel_monitoring(stream)

    def __enter__(self):
        raise RuntimeError('"yield from" should be used as context manager expression')

    def __exit__(self, *exc_args):
        # This must exist because __enter__ exists, even though __enter__ always raises.
        pass

    def __iter__(self):
        # This is not a coroutine.
        # It enables Server to be used as a with-statement context manager.
        # Method from asyncio.locks.Lock.
        yield from self.start()
        return _ContextManager(self)


class _ContextManager:
    # See asyncio.locks._ContextManager.
    def __init__(self, server):
        self._server = server

    def __enter__(self):
        debug('inside _ContextManager.__enter__')
        return self._server

    def __exit__(self, *exc_args):
        debug('inside _ContextManager.__exit__')
        try:
            debug('running coroutine Server.stop with asyncio.async')
            asyncio.async(self._server.stop(*exc_args), loop=self._server.loop)
        finally:
            self._server = None  # Crudely prevent reuse.

@asyncio.coroutine
def monitor_feed(monitor, feed):
    """
    Coroutine that calls a function on every line in a feed.
    When the function raises |StopIteration|, the coroutine returns.
    The coroutine will also return if an empty line is encountered.
    Therefore, this works best with methods like ``readline()`` that always include a newline.

    This function is a |coroutine|.

    Parameters
    ----------
    monitor : func
        Callable representing the monitoring step.
        Should take one argument, and raise |StopIteration| when it no longer wants to process the feed.
    feed : func
        Callable representing the feed.
        Should take no arguments.

    """
    if not _iscoroutinefunction(feed):
        debug('making type {} a coroutine'.format(type(feed).__name__))
        feed = asyncio.coroutine(feed)

    while True:
        debug('yielding from coroutine feed')
        line = yield from feed()
        if not line:
            return
        try:
            monitor(line)
        except StopIteration:
            return


@toolz.curry
def _check_for_pattern(pattern, line, log_func=None):
    if log_func:
        log_func(line)

    if re.search(pattern, line):
        raise StopIteration


def decoded_readline(stream):
    """
    Get a function similar to the ``readline()`` method, except that bytes are decoded.

    Parameters
    ----------
    stream : |asyncio.StreamReader| or file descriptor
        Any object with a ``readline()`` method.

    Returns
    -------
    func

    """
    if _iscoroutinefunction(stream.readline):
        return partial(_readline_decode_async, stream)
    else:
        return partial(_readline_decode_sync, stream)


@asyncio.coroutine
def _readline_decode_async(stream):
    debug('yielding from coroutine stream.readline')
    line = yield from stream.readline()
    return line.decode()


def _readline_decode_sync(stream):
    return stream.readline().decode()
