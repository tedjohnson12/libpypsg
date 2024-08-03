.. pypsg documentation master file, created by
   sphinx-quickstart on Fri Dec  1 08:30:39 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ``libpypsg``!
========================

``libpypsg`` is a Python library that acts as an interface to the Planetary Spectrum Generator (PSG). PSG is
used widely by astronomers and planetary scientists to create synthetic spectra
of exoplanets and solar system objects. The goal of this package is to make
PSG more accessible to new users, but still be powerful enough that expert
users will find it useful.

``libpypsg`` is not like other packages that submit configuration files to PSG. Its ``cfg`` module is based object-relational mapping frameworks,
which are usually used to connect a database to an application. Instead of mapping to a SQL database, however, objects in ``libpypsg`` 
map to PSG configuration files. This provides a simple and flexible interface that anyone with Python familiarity can use.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   intro
   api
   auto_examples/index



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
