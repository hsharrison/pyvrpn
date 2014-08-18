# -*- coding: utf-8 -*-
import re
import os
import sys

MOCK_MODULES = []

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinxcontrib.napoleon',
    'sphinx.ext.intersphinx',
]


class Mock(object):

    __all__ = []

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

    @classmethod
    def __getattr__(cls, name):
        if name in ('__file__', '__path__'):
            return '/dev/null'
        elif name[0] == name[0].upper():
            mockType = type(name, (), {})
            mockType.__module__ = __name__
            return mockType
        else:
            return Mock()

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()

if os.getenv('SPELLCHECK'):
    extensions += 'sphinxcontrib.spelling',
    spelling_show_suggestions = True
    spelling_lang = 'en_US'

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:
    html_theme = 'sphinx_rtd_theme'
    import sphinx_rtd_theme
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build']
html_static_path = ['_static']
templates_path = ['_templates']

project = 'pyvrpn'
copyright = '2014, Henry S. Harrison'

release = re.findall(
    '__version__ = "(.*)"',
    open(os.path.join(os.path.dirname(__file__), '../src/pyvrpn/__version__.py')).read()
)[0]
split_version = release.split('.')
split_version[-1] = re.match('[0-9]*', split_version[-1]).group(0)
version = '.'.join(split_version)

add_function_parentheses = False
pygments_style = 'sphinx'

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

intersphinx_mapping = {
    'python': ('http://docs.python.org/3/', None),
    'numpy': ('http://docs.scipy.org/doc/numpy/', None),
    'pandas': ('http://pandas.pydata.org/pandas-docs/stable/', None),
    'scipy': ('http://docs.scipy.org/doc/scipy/reference/', None),
}

rst_epilog = """

.. |asyncio.EventLoop| replace:: :class:`asyncio.EventLoop`
.. |asyncio.subprocess.Process| replace:: :class:`asyncio.subprocess.Process`
.. |asyncio.Task| replace:: :class:`asyncio.Task`
.. |coroutine| replace:: :func:`~asyncio.coroutine`
.. |asyncio.StreamReader| replace:: :class:`asyncio.StreamReader`
.. |asyncio| replace:: :mod:`asyncio`
.. |__exit__| replace:: :ref:`__exit__ <typecontextmanager>`
.. |traceback| replace:: :ref:`traceback`
.. |StopIteration| replace:: :class:`StopIteration`

.. |pyglet.event.EventDispatcher| replace:: :class:`pyglet.event.EventDispatcher`
.. |EventDispatcher| replace:: :class:`~pyglet.event.EventDispatcher`

.. |proc| replace:: :attr:`~pyvrpn.Server.proc`
.. |started_at| replace:: :attr:`~pyvrpn.Server.started_at`
.. |Server.start| replace:: :meth:`Server.start <pyvrpn.Server.start>`
.. |sentinel| replace:: :attr:`~pyvrpn.Server.sentinel`
.. |monitor_tasks| replace:: :attr:`~pyvrpn.Server.monitor_tasks`
.. |sleep| replace:: :attr:`~pyvrpn.Server.sleep`
.. |LocalServer| replace:: :class:`~pyvrpn.LocalServer`
.. |LocalServer.start| replace:: :meth:`LocalServer.start <pyvrpn.LocalServer.start>`

.. |device_type| replace:: :attr:`~pyvrpn.receiver.Receiver.device_type`
.. |object_class| replace:: :attr:`~pyvrpn.receiver.Receiver.object_class`
.. |n_sensors| replace:: :attr:`~pyvrpn.receiver.Receiver.n_sensors`
.. |extend_config_line_with_backslash| replace:: :attr:`~pyvrpn.receiver.Receiver.extend_config_line_with_backslash`
.. |mainloop| replace:: :meth:`~pyvprn.receiver.Receiver.mainloop`

.. |vrpn.receiver.Tracker| replace:: :class:`vrpn.receiver.Tracker`

.. |Sensor| replace:: :class:`~pyvrpn.receiver.Sensor`
.. |Receiver| replace:: :class:`~pyvrpn.receiver.Receiver`

"""
