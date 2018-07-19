#########################
Python SAGE Data Reader
#########################

Basic python reader for SAGE II and SAGE III binary data files into an `xarray` data structure or a dictionary of numpy
arrays. The binary files SAGE data files are not supplied and must be downloaded by the user. They can be found at the
`NASA ASDC <https://eosweb.larc.nasa.gov/project/sage2/sage2_v7_table?qt-sage2_aerosol_tabs=1#qt-sage2_aerosol_tabs/>`_
website.

Installation
************

To install the package from pypi run:
::

    pip install pysagereader


Basic Use
*********

An example of loading data from 2000 through 2003 between 10\ :sup:`o`\N and 10\ :sup:`o`\S ::

    from pySAGE.pysagereader.sage_ii_reader import SAGEIILoaderV700

    sage = SAGEIILoaderV700(data_folder=data_folder, filter_ozone=True, cf_names=True)
    data = sage.load_data('2000-1-1', '2003-12-31', -10, 10)
    data.O3.plot(x='time', robust=True)

