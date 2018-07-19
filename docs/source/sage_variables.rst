.. _sage_variables:


SAGE II
*******

Variables
=========

As far as possible the original SAGE II variable names used in the IDL scripts and
`documentation <https://eosweb.larc.nasa.gov/sites/default/files/project/sage2/readme/readme_sage2_v6.20.txt/>`_
have been adopted. If `xarray` is chosen as the output format revision and creation date information is not
included in the output structure.


Altitude Range for Species
--------------------------

=============== ==============
Species          Range (km)
=============== ==============
Ozone           5-60
NO2             15-60
Aerosol         1-45
Water Vapor     MSL-40
=============== ==============

Revision Info
-------------
==================  ========================================
Field                        Description
==================  ========================================
Num_Prof            Number of profiles (records) in file
Met_Rev_Date        LaRC Met Model Rev Date (yyyymmdd)
Driver_Rev          LaRC Driver version (eg. 6.20)
Transmission_Rev    LaRC Transmission version
Inversion_Rev       LaRC Inversion version
Spectroscopy_Rev    LaRC Inversion version
Eph_File_Name       Ephemeris file name
Met_File_Name       Met file name
Ref_File_Name       Refraction file name
Trans_File_Name     Transmission file name
Spec_File_Name      Species profile file name
FillVal             Fill value
==================  ========================================


Altitude grid and range info
----------------------------
================= ==================================
Grid_Size             Altitude Grid spacing
================= ==================================
Alt_Grid            Geometric Alt
Alt_Mid_Atm         Geometric Alt for Dens_Mid_Atm
Range_Trans         Transmission Min & Max alt
Range_O3            Ozone Density Min & Max alt
Range_NO2           NO2 Density Min & Max alt
Range_H2O           H2O Density Min & Max alt
Range_Ext           Extinction Min & Max alt
Range_Density       Density Min & Max alt
Range_Surface       Surface Area Min & Max alt
================= ==================================

Event Specific Info
-------------------
================== ===================================
YYYYMMDD            Event Date (yyyymmdd) at 30 km
event_num           The event number
HHMMSS              Event Time (hhmmss) at 30 km
Day_Frac            Time of Year (ddd.fraction)
Lat                 Sub-tangent Lat at 30km
Lon                 Sub-tangent Lon at 30km
Beta                Spacecraft Beta angle (degree
Duration            Duration of event (seconds)
Type_Sat            Instrument Event Type, 0=sr, 1=ss)
Type_Tan            Event Type, Local (0=sr,1=ss)
================== ===================================

Process Tracking Flag info
---------------------------
====================== =========================================
**Processing Success**
Dropped                Value is non-zero if event is dropped
InfVec                 32 bits describing the event processing
**Ephemeris**
Eph_Cre_Date           Record creation date (yyyymmdd)
Eph_Cre_Time           Record creation time (hhmmss)
**Met**
Met_Cre_Date           Record creation date (yyyymmdd)
Met_Cre_Time           Record creation time (hhmmss)
**Refraction**
Ref_Cre_Date           Record creation date (yyyymmdd)
Ref_Cre_Time           Record creation time (hhmmss)
**Transmission**
TRANS_Cre_Date         Record creation date (yyyymmdd)
TRANS_Cre_Time         Record creation time (hhmmss)
**Inversion**
SPECIES_Cre_Date       Record creation date (yyyymmdd)
SPECIES_Cre_Time       Record creation time (hhmmss)
====================== =========================================

Species File Contents
----------------------------
**Field Type Description**

================  ====================================================
Tan_Alt           Center-of-Sun Tangent Alt (km)
Tan_Lat           Center-of-Sun Lat (deg)
Tan_Lon           Center-of-Sun Lon (deg)
NMC_Pres          Pressure (mb) (0.5-70km)
NMC_Temp          Temperature (K), (0.5-70km)
NMC_Dens          Density (molecules/cm3) (.5-70km)
NMC_Dens_Err      Density Uncertainty(%x100)
Trop_Height       Tropopause height in km
Wavelength        Channel wavelengths
O3                O3 number density (cm-3)
NO2               NO2 number density (cm-3)
H2O               H2O number density (ppp)
Ext386            386 nm aerosol extinction (1/km)
Ext452            452 nm aerosol extinction (1/km)
Ext525            525 nm aerosol extinction (1/km)
Ext1020           1020 nm aerosol extinction (1/km)
Density           Molecular density (1/cm^3)
SurfDen           Aerosol surface area density  (micrometer^2/cm^3)
Radius            Aerosol effective radius (micrometer)
Dens_Mid_Atm      Middle atmosphere retrieved density(1/cm^3)
O3_Err            o3  number density uncertainty (%x100)
NO2_Err           NO2 number density uncertainty (%x100)
H2O_Err           H2O number density uncertainty (%x100)
Ext386_Err        386 nm aerosol ext. uncertainty (%x100)
Ext452_Err        452 nm aerosol ext. uncertainty (%x100)
Ext525_Err        525 nm aerosol ext. uncertainty (%x100)
Ext1020_Err       1020 nm aerosol ext. uncertainty (%x100)
Density_Err       Density uncertainty (%x100)
SurfDen_Err       Aerosol surface area density uncertainty(%x100)
Radius_Err        Aerosol effective radius uncertainty (%x100)
Dens_Mid_Atm_Err  Middle atmosphere density uncertainty (%x100)
InfVec            Bit-wise quality flags
================  ====================================================

Quality Flags
=============

SAGE II data returns both event (index) flags as well as species flags. These are 32 bit integers
contained in the `InfVec` and `ProfileInfVec` variables respectively. However, for easier use the
flags can be expanded to show each bit separately.

.. code-block:: python

    from pysagereader.sage_ii_reader import SAGEIILoaderV700

    sage = SAGEIILoaderV700(data_folder=r'path\to\sage\data', enumerate_flags=True)
    data = sage.load_data('2000-1-1', '2003-12-31', -10, 10)

The flags can also be returned in a separate array for convenience.

.. code-block:: python

    from pysagereader.sage_ii_reader import SAGEIILoaderV700

    sage = SAGEIILoaderV700(data_folder=r'path\to\sage\data', return_separate_flags=True)
    data, flags = sage.load_data('2000-1-1', '2003-12-31', -10, 10)


Data Filtering
==============

Ozone
-----

It is recommend that only a subset of the ozone data be used for scientific analysis, based on
filtering recommendations from the `release notes. <https://eosweb.larc.nasa.gov/project/sage2/sage2_release_v7_notes/>`_
Ozone results that meet these criteria can be determined from the `ozone_filter` variable in the returned
dataset. A value of `0` indicates ozone should not be used. The following criteria are used as the filters:

    * Exclusion of all data points with an uncertainty estimate of 300% or greater
    * Exclusion of all profiles with an uncertainty greater than 10% between 30 and 50 km
    * Exclusion of all data points at altitude and below the occurrence of an aerosol extinction value of
      greater than 0.006 km\ :sup:`-1`
    * Exclusion of all data points at altitude and below the occurrence of both the 525nm aerosol extinction
      value exceeding 0.001 km\ :sup:`-1` and the 525/1020 extinction ratio falling below 1.4
    * Exclusion of all data points below 35km an 200% or larger uncertainty estimate

Aerosol
-------

To remove cloud contamination from the aerosol data flags `Cloud_Bit_1` and `Cloud_Bit_2` are used to
compute the `cloud_filter`. A value of `1` indicates there is a cloud present at or above that altitude.