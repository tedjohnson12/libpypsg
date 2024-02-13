# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pypsg'
copyright = '2023, Ted Johnson, The PSG Team'
author = 'Ted Johnson, The PSG Team'
release = '0.1.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon',
    'sphinx_automodapi.automodapi',
    'sphinx_automodapi.smart_resolver',
    'numpydoc',
    'sphinx.ext.intersphinx',
    'sphinx_gallery.gen_gallery'
]

sphinx_gallery_conf = {
     'examples_dirs': ['../../examples'],   # path to your example scripts
     'gallery_dirs': ['auto_examples'],  # path to where to save gallery generated output
     'matplotlib_animations': True,
    #  'run_stale_examples': True,
}

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/',
               (None, 'http://data.astropy.org/intersphinx/python3.inv')),
    'numpy': ('https://numpy.org/doc/stable/',
              (None, 'http://data.astropy.org/intersphinx/numpy.inv')),
    'pandas': ('https://pandas.pydata.org/docs/',
              (None, 'http://data.astropy.org/intersphinx/pandas.inv')),
    'scipy': ('https://docs.scipy.org/doc/scipy/',
              (None, 'http://data.astropy.org/intersphinx/scipy.inv')),
    'matplotlib': ('https://matplotlib.org/stable/',
                   (None, 'http://data.astropy.org/intersphinx/matplotlib.inv')),
    'astropy': ('https://docs.astropy.org/en/stable/', None),
    'h5py': ('https://docs.h5py.org/en/stable/', None),
    'jax': ('https://jax.readthedocs.io/en/latest/', None),
    
}

numpydoc_show_class_members = False
autodoc_inherit_docstrings = True