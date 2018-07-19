#########################
Python SAGE Data Reader
#########################

|Documentation Status| |MIT license| |PyPI version fury.io|

.. |Documentation Status| image:: https://readthedocs.org/projects/pysagereader/badge/?version=latest
   :target: http://pysagereader.readthedocs.io/?badge=latest
   
.. |MIT license| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://lbesson.mit-license.org/
   
.. |PyPI version fury.io| image:: https://badge.fury.io/py/pysagereader.svg
    :target: https://badge.fury.io/py/pysagereader


Basic python reader for SAGE II and SAGE III binary data files into an `xarray` data structure or a dictionary of numpy
arrays. The binary files SAGE data files are not supplied and must be downloaded by the user. They can be found at the
`NASA ASDC <https://eosweb.larc.nasa.gov/project/sage2/sage2_v7_table?qt-sage2_aerosol_tabs=1#qt-sage2_aerosol_tabs/>`_
website.

Installation
************

To install the package from pypi run:
::

    pip install pysagereader

Documentation
*************

https://pysagereader.readthedocs.io/en/latest/


Basic Use
*********

An example of loading data from 2000 through 2003 between 10\ :sup:`o`\N and 10\ :sup:`o`\S ::

    from pySAGE.pysagereader.sage_ii_reader import SAGEIILoaderV700

    sage = SAGEIILoaderV700(data_folder=data_folder, filter_ozone=True, cf_names=True)
    data = sage.load_data('2000-1-1', '2003-12-31', -10, 10)
    data.O3.plot(x='time', robust=True)

