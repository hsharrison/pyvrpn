import pyvrpn.logging


def redirect(*args):
    return pyvrpn.logging.get_lineno_from_deeper_in_stack(*args)


def test_dereference_lineno():
    assert redirect(1, 5) == 9
    assert redirect(1, 5, 'redirect') == 10


def test_dereference_lineno_wrong_func():
    assert redirect(1, 5, 'test_dereference_lineno_wrong_func') == 5
