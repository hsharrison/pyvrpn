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