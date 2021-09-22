.. _quickstart:


Quickstart
**********

Get the data
============
The SAGE II data is not provided with the pysagereader package but can be obtained from `NASA ASDC. <https://asdc.larc.nasa.gov/project/SAGE%20II/SAGE2_AEROSOL_O3_NO2_H2O_BINARY_V7.0>`_

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
