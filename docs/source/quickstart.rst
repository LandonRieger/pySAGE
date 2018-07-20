.. _quickstart:


Quickstart
**********

Get the data
============
The SAGE II data is not provided with the pysagereader package but can be obtained from `NASA ASDC. <https://eosweb.larc.nasa.gov/project/sage2/sage2_v7_table?qt-sage2_aerosol_tabs=1#qt-sage2_aerosol_tabs/>`_

Install the package
===================
To install the package from PyPI

.. code-block:: python

   pip install pysagereader


Loading the data
================

By default data is loaded into an xarray dataset that can be easily sliced, subset, and plotted.

.. code-block:: python

   from pysagereader import SAGEIILoaderV700
   sage = SAGEIILoaderV700(data_folder=r'/path/to/sage/data')
   data = sage.load_data(min_date='2000-1-1', max_date='2003-12-31', min_lat=-10, max_lat=10)
   data.O3.plot(x='time', robust=True)


Creating NetCDF files
=====================

The xarray package also provides convenient export to NetCDF files

.. code-block:: python

   from pysagereader import SAGEIILoaderV700
   sage = SAGEIILoaderV700(data_folder=r'/path/to/sage/data')
   data = sage.load_data(min_date='2000-1-1', max_date='2001-12-31')
   data.to_netcdf('sage_ii_v700_2000.nc')

Or from the command line::

    python /install/directory/pysagereader/make_netcdf.py -i /sageii/data/folder -o /output/folder -time_res yearly
