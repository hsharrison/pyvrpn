import logging
import inspect


try:
    import cytoolz as toolz
except ImportError:
    import toolz


@toolz.curry
def log_rstrip(logger, level, message):
    logger.log(level, str(message).rstrip())


def get_lineno_from_deeper_in_stack(n_frames_offset, original_lineno, func_name=None):
    """
    Given a line number, find the frame in the stack that it refers to,
    and return the line number from a frame deeper in the stack.
    If `func_name` is passed, change the line number only if the original frame references the named function.
    Useful for replacing the line number of a custom logging function
    with the line number of the *call* to that function.
    In other words, dereferencing a logging call.

    Parameters
    ----------
    n_frames_offset : int
    original_lineno : int
    func_name : str, optional

    Returns
    -------
    int

    """
    frames = inspect.stack()
    original_frame_ix = next(ix for ix, frame in enumerate(frames) if frame[2] == original_lineno)
    if func_name is None or frames[original_frame_ix][3] == func_name:
        return frames[original_frame_ix + n_frames_offset][2]
    return original_lineno


def setup_module_logging(name, levels=(logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)):
    """
    Do all the necessary setup for a module.
    Dereferences the record factory, and returns four logging functions.

    Parameters
    ----------
    name : str

    Returns
    -------
    error : func
    warning : func
    info : func
    debug : func

    """
    original_record_factory = logging.getLogRecordFactory()

    def dereferenced_log_record_factory(*args, **kwargs):
        record = original_record_factory(*args, **kwargs)
        record.lineno = get_lineno_from_deeper_in_stack(1, record.lineno, 'log_rstrip')
        return record

    logging.setLogRecordFactory(dereferenced_log_record_factory)

    module_logger = log_rstrip(logging.getLogger(name))
    return tuple(module_logger(level) for level in levels)
