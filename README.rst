#########################
Python SAGE Data Reader
#########################

Basic python reader for SAGE II and SAGE III binary data files into a dictionary of numpy arrays.
The binary files are not supplied and must be downloaded by the user. They can be found at the 
`NASA ASDC <https://eosweb.larc.nasa.gov/project/sage2/sage2_v7_table?qt-sage2_aerosol_tabs=1#qt-sage2_aerosol_tabs/>`_

pysagereader is used to read the binary files supplied by ASDC into a python dictionary of numpy arrays.


Installation
************

To install the package from pypi run:
::

    pip install pysagereader

SAGE II Reader
**************
As far as possible the original SAGE II variable names used in the original IDL scripts and `documentation <https://eosweb.larc.nasa.gov/sites/default/files/project/sage2/readme/readme_sage2_v6.20.txt/>`_ have been adopted.

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
Ephemeris:
Eph_Cre_Date           Record creation date (yyyymmdd)
Eph_Cre_Time           Record creation time (hhmmss)
**Met**
Met_Cre_Date           Record creation date (yyyymmdd)
Met_Cre_Time           Record creation time (hhmmss)
Refraction:
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

Basic Use
*********

An example of loading data from 2000 through 2003 between 10\ :sup:`o`\N and 10\ :sup:`o`\S ::

    from pysagereader.sageiireader import SAGEIILoaderV700
    import matplotlib.pyplot as plt

    sage = SAGEIILoaderV700()
    sage.data_folder = data_folder
    data = sage.load_data('2000-1-1','2003-12-31', -10,10)

    #replace bad data with nans
    data['O3'][data['O3'] == data['FillVal']] = np.nan
    data['O3'][data['O3_Err']>10000]       = np.nan

    #get ozone altitudes
    o3_alts = data['Alt_Grid'][(data['Alt_Grid'] >= data['Range_O3'][0]) & (data['Alt_Grid'] <= data['Range_O3'][1])]
