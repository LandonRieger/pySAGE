import numpy as np
import xarray as xr
import pandas as pd
import os
from collections import OrderedDict
# from astropy.time import Time
import logging
import copy
from typing import List, Dict, Union, Tuple
import pysagereader


class SAGEIILoaderV700(object):
    """
    Class designed to load the v7.00 SAGE II spec and index files provided by NASA ADSC into python

    Data files must be accessible by the users machine, and can be downloaded from:
    https://eosweb.larc.nasa.gov/project/sage2/sage2_v7_table

    Parameters
    ----------
    data_folder
        location of sage ii index and spec files.
    output_format
        format for the output data. If ``'xarray'`` the output is returned as an ``xarray.Dataset``.
        If None the output is returned as a dictionary of numpy arrays.

        **NOTE: the following options only apply to xarray output types**
    species
        Species to be returned in the output data. If None all species are returned. Options are
        ``aerosol``, ``ozone``, ``h2o``, and ``no2``. If more than one species is returned fields will be NaN-padded
        where data is not available. ``species`` is only used if ``'xarray'`` is set as the ``output_data`` format,
        otherwise it has no effect.
    cf_names
        If True then CF-1.7 naming conventions are used for the output_data when ``xarray`` is selected.
    filter_aerosol
        filter the aerosol using the cloud flag
    filter_ozone
        filter the ozone using the criteria recommended in the release notes

            * Exclusion of all data points with an uncertainty estimate of 300% or greater
            * Exclusion of all profiles with an uncertainty greater than 10% between 30 and 50 km
            * Exclusion of all data points at altitude and below the occurrence of an aerosol extinction value of
              greater than 0.006 km^-1
            * Exclusion of all data points at altitude and below the occurrence of both the 525nm aerosol extinction
              value exceeding 0.001 km^-1 and the 525/1020 extinction ratio falling below 1.4
            * Exclusion of all data points below 35km an 200% or larger uncertainty estimate
    enumerate_flags
        expand the index and species flags to their boolean values.
    normalize_percent_error
        give the species error as percent rather than percent * 100
    return_separate_flags
        return the enumerated flags as a separate data array

    Example
    -------

    >>> sage = SAGEIILoaderV700()
    >>> sage.data_folder = 'path/to/data'
    >>> data = sage.load_data('2004-1-1','2004-5-1')

    In addition to the sage ii fields reported in the files, two additional time fields are provided
    to allow for easier subsetting of the data.

    ``data['mjd']`` is a numpy array containing the modified julian dates of each scan

    ``date['time']`` is an pandas time series object containing the times of each scan

    """
    def __init__(self, data_folder: str = None,
                 output_format: str = 'xarray',
                 species: List[str] = ('aerosol', 'h2o', 'no2', 'ozone', 'background'),
                 cf_names: bool = False,
                 filter_aerosol: bool = False,
                 filter_ozone: bool = False,
                 enumerate_flags: bool = False,
                 normalize_percent_error: bool = False,
                 return_separate_flags: bool = False):

        if type(species) == str:
            species = [species]

        self.data_folder = data_folder  # Type: str
        self.version = '7.00'
        self.index_file = 'SAGE_II_INDEX_'
        self.spec_file = 'SAGE_II_SPEC_'

        self.fill_value = np.nan

        self.spec_format = self.get_spec_format()
        self.index_format = self.get_index_format()
        self.output_format = output_format
        self.species = [s.lower() for s in species]
        self.cf_names = cf_names
        self.filter_aerosol = filter_aerosol
        self.filter_ozone = filter_ozone
        self.normalize_percent_error = normalize_percent_error
        self.enumerate_flags = enumerate_flags
        self.return_separate_flags = return_separate_flags

    @staticmethod
    def get_spec_format() -> Dict[str, Tuple[str, int]]:
        """
        spec format taken from sg2_specinfo.pro provided in the v7.00 download

        used for reading the binary data format

        Returns
        -------
        Dict
            Ordered dictionary of variables provided in the spec file. Each dictionary field contains a
            tuple with the information (data type, number of data points). Ordering is important as the
            sage ii binary files are read sequentially.
        """
        spec = OrderedDict()
        spec['Tan_Alt'] = ('float32', 8)       # Subtangent Altitudes(km)
        spec['Tan_Lat'] = ('float32', 8)       # Subtangent Latitudes @ Tan_Alt(deg)
        spec['Tan_Lon'] = ('float32', 8)       # Subtangent Longitudes @ Tan_Alt(deg)

        spec['NMC_Pres'] = ('float32', 140)    # Gridded Pressure profile(mb)
        spec['NMC_Temp'] = ('float32', 140)    # Gridded Temperature profile(K)
        spec['NMC_Dens'] = ('float32', 140)    # Gridded Density profile(cm ^ (-3))
        spec['NMC_Dens_Err'] = ('int16', 140)  # Error in NMC_Dens( % * 1000)

        spec['Trop_Height'] = ('float32', 1)   # NMC Tropopause Height(km)
        spec['Wavelength'] = ('float32', 7)    # Wavelength of each channel(nm)

        spec['O3'] = ('float32', 140)          # O3 Density profile 0 - 70 Km(cm ^ (-3))
        spec['NO2'] = ('float32', 100)         # NO2 Density profile 0 - 50 Km(cm ^ (-3))
        spec['H2O'] = ('float32', 100)         # H2O Volume Mixing Ratio 0 - 50 Km(ppp)

        spec['Ext386'] = ('float32', 80)       # 386 nm Extinction 0 - 40 Km(1 / km)
        spec['Ext452'] = ('float32', 80)       # 452 nm Extinction 0 - 40 Km(1 / km)
        spec['Ext525'] = ('float32', 80)       # 525 nm Extinction 0 - 40 Km(1 / km)
        spec['Ext1020'] = ('float32', 80)      # 1020 nm Extinction 0 - 40 Km(1 / km)
        spec['Density'] = ('float32', 140)     # Calculated Density 0 - 70 Km(cm ^ (-3))
        spec['SurfDen'] = ('float32', 80)      # Aerosol surface area dens 0 - 40 km(um ^ 2 / cm ^ 3)
        spec['Radius'] = ('float32', 80)       # Aerosol effective radius 0 - 40 km(um)

        spec['Dens_Mid_Atm'] = ('float32', 70)  # Middle Atmosphere Density(cm ^ (-3))
        spec['O3_Err'] = ('int16', 140)        # Error in O3 density profile( % * 100)
        spec['NO2_Err'] = ('int16', 100)       # Error in NO2 density profile( % * 100)
        spec['H2O_Err'] = ('int16', 100)       # Error in H2O mixing ratio( % * 100)

        spec['Ext386_Err'] = ('int16', 80)     # Error in 386 nm Extinction( % * 100)
        spec['Ext452_Err'] = ('int16', 80)     # Error in 452 nm Extinction( % * 100)
        spec['Ext525_Err'] = ('int16', 80)     # Error in 525 nm Extinction( % * 100)
        spec['Ext1020_Err'] = ('int16', 80)    # Error in 1019 nm Extinction( % * 100)
        spec['Density_Err'] = ('int16', 140)   # Error in Density( % * 100)
        spec['SurfDen_Err'] = ('int16', 80)    # Error in surface area dens( % * 100)
        spec['Radius_Err'] = ('int16', 80)     # Error in aerosol radius( % * 100)

        spec['Dens_Mid_Atm_Err'] = ('int16', 70)  # Error in Middle Atm.Density( % * 100)
        spec['InfVec'] = ('uint16', 140)       # Informational Bit flags

        return spec

    @staticmethod
    def get_index_format() -> Dict[str, Tuple[str, int]]:
        """
        index format taken from sg2_indexinfo.pro provided in the v7.00 download

        used for reading the binary data format

        Returns
        -------
        Dict
            an ordered dictionary of variables provided in the index file. Each dictionary
            field contains a tuple with the information (data type, length). Ordering is
            important as the sage ii binary files are read sequentially.
        """

        info = OrderedDict()

        info['num_prof'] = ('uint32', 1)       # Number of profiles in these files
        info['Met_Rev_Date'] = ('uint32', 1)   # LaRC Met Model Revision Date(YYYYMMDD)
        info['Driver_Rev'] = ('S1', 8)       # LaRC Driver Version(e.g. 6.20)
        info['Trans_Rev'] = ('S1', 8)        # LaRC Transmission Version
        info['Inv_Rev'] = ('S1', 8)          # LaRC Inversion Version
        info['Spec_Rev'] = ('S1', 8)         # LaRC Inversion Version
        info['Eph_File_Name'] = ('S1', 32)   # Ephemeris data file name
        info['Met_File_Name'] = ('S1', 32)   # Meteorological data file name
        info['Ref_File_Name'] = ('S1', 32)   # Refraction data file name
        info['Tran_File_Name'] = ('S1', 32)  # Transmission data file name
        info['Spec_File_Name'] = ('S1', 32)  # Species profile file name
        info['FillVal'] = ('float32', 1)       # Fill value

        # Altitude grid and range info
        info['Grid_Size'] = ('float32', 1)     # Altitude grid spacing(0.5 km)
        info['Alt_Grid'] = ('float32', 200)    # Geometric altitudes(0.5, 1.0, ..., 100.0 km)
        info['Alt_Mid_Atm'] = ('float32', 70)  # Middle atmosphere geometric altitudes
        info['Range_Trans'] = ('float32', 2)   # Transmission min & max altitudes[0.5, 100.]
        info['Range_O3'] = ('float32', 2)      # Ozone min & max altitudes[0.5, 70.0]
        info['Range_NO2'] = ('float32', 2)     # NO2 min & max altitudes[0.5, 50.0]
        info['Range_H2O'] = ('float32', 2)     # Water vapor min & max altitudes[0.5, 50.0]
        info['Range_Ext'] = ('float32', 2)     # Aerosol extinction min & max altitudes[0.5, 40.0]
        info['Range_Dens'] = ('float32', 2)    # Density min & max altitudes[0.5, 70.0]
        info['Spare'] = ('float32', 2)         #

        # Event specific info useful for data subsetting
        info['YYYYMMDD'] = ('int32', 930)      # Event date at 20km subtangent point
        info['Event_Num'] = ('int32', 930)     # Event number
        info['HHMMSS'] = ('int32', 930)        # Event time at 20km
        info['Day_Frac'] = ('float32', 930)    # Time of year(DDD.frac) at 20 km
        info['Lat'] = ('float32', 930)         # Subtangent latitude at 20 km(-90, +90)
        info['Lon'] = ('float32', 930)         # Subtangent longitude at 20 km(-180, +180)
        info['Beta'] = ('float32', 930)        # Spacecraft beta angle(deg)
        info['Duration'] = ('float32', 930)    # Duration of event(sec)
        info['Type_Sat'] = ('int16', 930)      # Event Type Instrument(0 = SR, 1 = SS)
        info['Type_Tan'] = ('int16', 930)      # Event Type Local(0 = SR, 1 = SS)

        # Process tracking and flag info
        info['Dropped'] = ('int32', 930)       # Dropped event flag
        info['InfVec'] = ('uint32', 930)       # Bit flags relating to processing (
        # NOTE: readme_sage2_v6.20.txt says InfVec is 16 bit but appears to actually be 32 (also in IDL software)

        # Record creation dates and times
        info['Eph_Cre_Date'] = ('int32', 930)  # Record creation date(YYYYMMDD format)
        info['Eph_Cre_Time'] = ('int32', 930)  # Record creation time(HHMMSS format)
        info['Met_Cre_Date'] = ('int32', 930)  # Record creation date(YYYYMMDD format)
        info['Met_Cre_Time'] = ('int32', 930)  # Record creation time(HHMMSS format)
        info['Ref_Cre_Date'] = ('int32', 930)  # Record creation date(YYYYMMDD format)
        info['Ref_Cre_Time'] = ('int32', 930)  # Record creation time(HHMMSS format)
        info['Tran_Cre_Date'] = ('int32', 930)  # Record creation date(YYYYMMDD format)
        info['Tran_Cre_Time'] = ('int32', 930)  # Record creation time(HHMMSS format)
        info['Spec_Cre_Date'] = ('int32', 930)  # Record creation date(YYYYMMDD format)
        info['Spec_Cre_Time'] = ('int32', 930)  # Record creation time(HHMMSS format)

        return info

    def get_spec_filename(self, year: int, month: int) -> str:
        """
        Returns the spec filename given a year and month

        Parameters
        ----------
        year
            year of the data that will be loaded
        month
            month of the data that will be loaded

        Returns
        -------
            filename of the spec file where the data is stored
        """
        file = os.path.join(self.data_folder,
                            self.spec_file + str(int(year)) + str(int(month)).zfill(2) + '.' + self.version)

        if not os.path.isfile(file):
            file = None

        return file

    def get_index_filename(self, year: int, month: int) -> str:
        """
        Returns the index filename given a year and month

        Parameters
        ----------
        year
            year of the data that will be loaded
        month
            month of the data that will be loaded

        Returns
        -------
            filename of the index file where the data is stored
        """

        file = os.path.join(self.data_folder,
                            self.index_file + str(int(year)) + str(int(month)).zfill(2) + '.' + self.version)

        if not os.path.isfile(file):
            file = None

        return file

    def read_spec_file(self, file: str, num_profiles: int) -> List[Dict]:
        """

        Parameters
        ----------
        file
            name of the spec file to be read
        num_profiles
            number of profiles to read from the spec file (usually determined from the index file)

        Returns
        -------
            list of dictionaries containing the spec data. Each list is one event
        """

        # load the file into the buffer
        file_format = self.spec_format
        with open(file, "rb") as f:
            buffer = f.read()

        # initialize the list of dictionaries
        data = [None] * num_profiles
        for p in range(num_profiles):
            data[p] = dict()

        # load the data from the buffer
        bidx = 0
        for p in range(num_profiles):
            for key in file_format.keys():
                nbytes = np.dtype(file_format[key][0]).itemsize * file_format[key][1]
                data[p][key] = copy.copy(np.frombuffer(buffer[bidx:bidx + nbytes],
                                                       dtype=file_format[key][0]))
                bidx += nbytes

        return data

    def read_index_file(self, file: str) -> Dict:
        """
        Read the binary file into a python data structure

        Parameters
        ----------
        file
            filename to be read

        Returns
        -------
            data from the file
        """

        file_format = self.index_format
        with open(file, "rb") as f:
            buffer = f.read()

        data = dict()

        # load the data from file into a list
        bidx = 0
        for key in file_format.keys():
            nbytes = np.dtype(file_format[key][0]).itemsize * file_format[key][1]
            if file_format[key][0] == 'S1':
                data[key] = copy.copy(buffer[bidx:bidx + nbytes].decode('utf-8'))
            else:
                data[key] = copy.copy(np.frombuffer(buffer[bidx:bidx + nbytes], dtype=file_format[key][0]))
                if len(data[key]) == 1:
                    data[key] = data[key][0]
            bidx += nbytes

        # make a more useable time field
        date_str = []
        # If the time overflows by less than the scan time just set it to midnight
        data['HHMMSS'][(data['HHMMSS'] >= 240000) & (data['HHMMSS'] < (240000 + data['Duration']))] = 235959
        # otherwise, set it as invalid
        data['HHMMSS'][data['HHMMSS'] >= 240000] = -999
        for idx, (ymd, hms) in enumerate(zip(data['YYYYMMDD'], data['HHMMSS'])):
            if (ymd < 0) | (hms < 0):
                date_str.append('1970-1-1 00:00:00')    # invalid sage ii date
            else:
                hours = int(hms / 10000)
                mins = int((hms % 10000) / 100)
                secs = hms % 100
                date_str.append(str(ymd)[0:4] + '-' + str(ymd)[4:6].zfill(2) + '-' +
                                str(ymd)[6::].zfill(2) + ' ' + str(hours).zfill(2) + ':' +
                                str(mins).zfill(2) + ':' + str(secs).zfill(2))

        # data['time'] = Time(date_str, format='iso')
        data['time'] = pd.to_datetime(date_str)
        data['mjd'] = np.array((data['time'] - pd.Timestamp('1858-11-17')) / pd.Timedelta(1, 'D'))
        data['mjd'][data['mjd'] < 40588] = -999  # get rid of invalid dates

        return data

    def load_data(self, min_date: str, max_date: str,
                  min_lat: float = -90, max_lat: float = 90,
                  min_lon: float = -180, max_lon: float = 360) -> Union[Dict, xr.Dataset]:
        """
        Load the SAGE II data for the specified dates and locations.

        Parameters
        ----------
        min_date
            start date where data will be loaded in iso format, eg: '2004-1-1'
        max_date
            end date where data will be loaded in iso format, eg: '2004-1-1'
        min_lat
            minimum latitude (optional)
        max_lat
            maximum latitude (optional)
        min_lon
            minimum longitude (optional)
        max_lon
            maximum longitude (optional)

        Returns
        -------
            Variables are returned as numpy arrays (1 or 2 dimensional depending on the variable)
        """
        min_time = pd.Timestamp(min_date)
        max_time = pd.Timestamp(max_date)
        data = dict()
        init = False

        # create a list of unique year/month combinations between the start/end dates
        uniq = OrderedDict()
        for year in [(t.date().year, t.date().month) for t in
                     pd.date_range(min_time, max_time + pd.Timedelta(27, 'D'), freq='27D')]:
            uniq[year] = year

        # load in the data from the desired months
        for (year, month) in list(uniq.values()):

            logging.info('loading data for : ' + str(year) + '/' + str(month))
            indx_file = self.get_index_filename(year, month)

            # if the file does not exist move on to the next month
            if indx_file is None:
                continue

            indx_data = self.read_index_file(indx_file)
            numprof = indx_data['num_prof']
            spec_data = self.read_spec_file(self.get_spec_filename(year, month), numprof)

            # get rid of the duplicate names for InfVec
            for sp in spec_data:
                sp['ProfileInfVec'] = copy.copy(sp['InfVec'])
                del sp['InfVec']

            for key in indx_data.keys():
                # get rid of extraneous profiles in the index so index and spec are the same lengths
                if hasattr(indx_data[key], '__len__') and type(indx_data[key]) is not str:
                    if len(indx_data[key]) == 930:
                        indx_data[key] = np.delete(indx_data[key], np.arange(numprof, 930))

                # add the index values to the data set
                if key in data.keys():
                    # we dont want to replicate certain fields
                    if (key[0:3] != 'Alt') & (key[0:5] != 'Range') & (key[0:7] != 'FillVal'):
                        data[key] = np.append(data[key], indx_data[key])
                else:
                    if key == 'FillVal':
                        data[key] = indx_data[key]
                    else:
                        data[key] = [indx_data[key]]

            # initialize the data dictionaries as lists
            if init is False:
                for key in spec_data[0].keys():
                    data[key] = []
                init = True

            # add the spec values to the data set
            for key in spec_data[0].keys():
                data[key].append(np.asarray([sp[key] for sp in spec_data]))

        # join all of our lists into an array - this could be done more elegantly with vstack to avoid
        # the temporary lists, but this is much faster
        for key in data.keys():
            if key == 'FillVal':
                data[key] = float(data[key])  # make this a simple float rather than zero dimensional array
            elif type(data[key][0]) is str:
                data[key] = str(data[key][0])
            elif len(data[key][0].shape) > 0:
                data[key] = np.concatenate(data[key], axis=0)
            else:
                data[key] = np.asarray(data[key])

        data = self.subset_data(data, min_date, max_date, min_lat, max_lat, min_lon, max_lon)
        if not data:
            return None

        if self.output_format == 'xarray':
            data = self.convert_to_xarray(data)

        return data

    @staticmethod
    def subset_data(data: Dict, min_date: str, max_date: str,
                    min_lat: float, max_lat: float,
                    min_lon: float, max_lon: float) -> Dict:
        """
        Removes any data from the dictionary that does not meet the specified time, latitude and longitude requirements.

        Parameters
        ----------
        data
            dictionary of sage ii data. Must have the fields 'mjd', 'Lat' and 'Lon'. All others are optional
        min_date
            start date where data will be loaded in iso format, eg: '2004-1-1'
        max_date
            end date where data will be loaded in iso format, eg: '2004-1-1'
        min_lat
            minimum latitude (optional)
        max_lat
            maximum latitude (optional)
        min_lon
            minimum longitude (optional)
        max_lon
            maximum longitude (optional)

        Returns
        -------
            returns the dictionary with only data in the valid latitude, longitude and time range
        """
        min_mjd = (pd.Timestamp(min_date) - pd.Timestamp('1858-11-17')) / pd.Timedelta(1, 'D')
        max_mjd = (pd.Timestamp(max_date) - pd.Timestamp('1858-11-17')) / pd.Timedelta(1, 'D')

        good = (data['mjd'] > min_mjd) & (data['mjd'] < max_mjd) & \
               (data['Lat'] > min_lat) & (data['Lat'] < max_lat) & \
               (data['Lon'] > min_lon) & (data['Lon'] < max_lon)

        if np.any(good):
            for key in data.keys():
                if type(data[key]) is str:
                    pass
                elif hasattr(data[key], '__len__'):
                    if data[key].shape[0] == len(good):
                        data[key] = data[key][good]
        else:
            print('no data satisfies the criteria')
            data = {}

        return data

    def convert_to_xarray(self, data: Dict) -> Union[xr.Dataset, Tuple[xr.Dataset, xr.Dataset]]:
        """
        Parameters
        ----------
        data
            Data from the ``load_data`` function

        Returns
        -------
            data formatted to an xarray Dataset
        """

        # split up the fields into one of different sizes and optional returns
        fields = dict()

        # not currently returned
        fields['geometry'] = ['Tan_Alt', 'Tan_Lat', 'Tan_Lon']
        fields['flags'] = ['InfVec', 'Dropped']
        fields['profile_flags'] = ['ProfileInfVec']

        # always returned - 1 per profile
        fields['general'] = ['Event_Num', 'Lat', 'Lon', 'Beta', 'Duration', 'Type_Sat', 'Type_Tan', 'Trop_Height']

        # optional return parameters
        fields['background'] = ['NMC_Pres', 'NMC_Temp', 'NMC_Dens', 'NMC_Dens_Err', 'Density', 'Density_Err']
        fields['ozone'] = ['O3', 'O3_Err']
        fields['no2'] = ['NO2', 'NO2_Err']
        fields['h2o'] = ['H2O', 'H2O_Err']
        fields['aerosol'] = ['Ext386', 'Ext452', 'Ext525', 'Ext1020', 'Ext386_Err', 'Ext452_Err', 'Ext525_Err',
                             'Ext1020_Err']
        fields['particle_size'] = ['SurfDen', 'Radius', 'SurfDen_Err', 'Radius_Err']

        xr_data = []
        index_flags = self.convert_index_bit_flags(data)
        species_flags = self.convert_species_bit_flags(data)
        time = pd.to_timedelta(data['mjd'], 'D') + pd.Timestamp('1858-11-17')

        data['Trop_Height'] = data['Trop_Height'].flatten()
        for key in fields['general']:
            xr_data.append(xr.DataArray(data[key], coords=[time], dims=['time'], name=key))

        if 'aerosol' in self.species or self.filter_ozone:  # we need aerosol to filter ozone
            altitude = data['Alt_Grid'][0:80]
            wavel = np.array([386.0, 452.0, 525.0, 1020.0])
            ext = np.array([data['Ext386'], data['Ext452'], data['Ext525'], data['Ext1020']])
            xr_data.append(xr.DataArray(ext, coords=[wavel, time, altitude],
                                        dims=['wavelength', 'time', 'Alt_Grid'], name='Ext'))
            ext = np.array([data['Ext386_Err'], data['Ext452_Err'], data['Ext525_Err'], data['Ext1020_Err']])
            xr_data.append(xr.DataArray(ext, coords=[wavel, time, altitude],
                                        dims=['wavelength', 'time', 'Alt_Grid'], name='Ext_Err'))
            for key in fields['particle_size']:
                xr_data.append(xr.DataArray(data[key], coords=[time, altitude],
                                            dims=['time', 'Alt_Grid'], name=key))
        if 'no2' in self.species:
            altitude = data['Alt_Grid'][0:100]
            for key in fields['no2']:
                xr_data.append(xr.DataArray(data[key], coords=[time, altitude],
                                            dims=['time', 'Alt_Grid'], name=key))
        if 'h2o' in self.species:
            altitude = data['Alt_Grid'][0:100]
            for key in fields['h2o']:
                xr_data.append(xr.DataArray(data[key], coords=[time, altitude],
                                            dims=['time', 'Alt_Grid'], name=key))
        if any(i in ['ozone', 'o3'] for i in self.species):
            altitude = data['Alt_Grid'][0:140]
            for key in fields['ozone']:
                xr_data.append(xr.DataArray(data[key], coords=[time, altitude],
                                            dims=['time', 'Alt_Grid'], name=key))

        if 'background' in self.species:
            altitude = data['Alt_Grid'][0:140]
            for key in fields['background']:
                xr_data.append(xr.DataArray(data[key], coords=[time, altitude],
                                            dims=['time', 'Alt_Grid'], name=key))

        xr_data = xr.merge(xr_data)

        if self.enumerate_flags:
            xr_data = xr.merge([xr_data, index_flags, species_flags])

        for var in xr_data.variables.keys():
            if xr_data[var].dtype == 'float32' or 'Err' in var:
                xr_data[var] = xr_data[var].where(xr_data[var] != data['FillVal'])

        # determine cloud filter for aerosol data
        cloud_filter = xr.full_like(species_flags.Cloud_Bit_1, fill_value=True, dtype=bool)
        min_alt = (xr_data.Alt_Grid * (species_flags.Cloud_Bit_1 & species_flags.Cloud_Bit_2)).max(dim='Alt_Grid')
        cloud_filter = cloud_filter.where(cloud_filter.Alt_Grid > min_alt)
        xr_data['cloud_filter'] = np.isnan(cloud_filter)

        # determine valid ozone altitudes
        if any(i in ['ozone', 'o3'] for i in self.species):
            # add an ozone filter field for convenience
            ozone_good = xr.full_like(species_flags.Cloud_Bit_1, fill_value=True, dtype=bool)
            # Exclusion of all data points with an uncertainty estimate of 300% or greater
            ozone_good = ozone_good.where(xr_data.O3_Err < 30000)
            # Exclusion of all profiles with an uncertainty greater than 10% between 30 and 50 km
            no_good = (xr_data.O3_Err > 1000) & (xr_data.Alt_Grid > 30) & (xr_data.Alt_Grid < 50)
            ozone_good = ozone_good.where(~no_good)
            # Exclusion of all data points at altitude and below the occurrence of an aerosol extinction value of
            # greater than 0.006 km^-1
            # NOTE: the wavelength to use as the filter is not specified in the documentation, so I have chosen the
            # wavelength with the smallest extinction and therefore the strictest filtering
            min_alt = (xr_data.Alt_Grid * (xr_data.Ext.sel(wavelength=1020) > 0.006)).max(dim='Alt_Grid')
            ozone_good = ozone_good.where(xr_data.Alt_Grid > min_alt)
            # Exclusion of all data points at altitude and below the occurrence of both the 525nm aerosol extinction
            # value exceeding 0.001 km^-1 and the 525/1020 extinction ratio falling below 1.4
            min_alt = (xr_data.Alt_Grid * ((xr_data.Ext.sel(wavelength=525) > 0.001) &
                                           ((xr_data.Ext.sel(wavelength=525) / xr_data.Ext.sel(
                                               wavelength=1020)) < 1.4))).max(dim='Alt_Grid')
            ozone_good = ozone_good.where(xr_data.Alt_Grid > min_alt)
            # Exclusion of all data points below 35km an 200% or larger uncertainty estimate
            no_good = (xr_data.O3_Err > 20000) & (xr_data.Alt_Grid < 35)
            ozone_good = ~np.isnan(ozone_good.where(~no_good))
            xr_data['ozone_filter'] = ozone_good

        if self.filter_aerosol:
            xr_data['Ext'] = xr_data.Ext.where(~xr_data.cloud_filter)

        if self.filter_ozone:
            xr_data['O3'] = xr_data.O3.where(ozone_good)

        # drop aerosol if not requested
        if self.filter_ozone and not ('aerosol' in self.species):
            xr_data.drop(['Ext', 'Ext_Err', 'wavelength'])

        if self.normalize_percent_error:
            for var in xr_data.variables.keys():
                if 'Err' in var:  # put error units back into percent
                    xr_data[var] = (xr_data[var] / 100).astype('float32')

        xr_data = xr_data.transpose('time', 'Alt_Grid', 'wavelength')
        xr_data = self.apply_cf_conventions(xr_data)

        if self.return_separate_flags:
            return xr_data, xr.merge([index_flags, species_flags])
        else:
            return xr_data

    def apply_cf_conventions(self, data):

        attrs = {'time': {'standard_name': 'time'},
                 'Lat': {'standard_name': 'latitude',
                         'units': 'degrees_north'},
                 'Lon': {'standard_name': 'longitude',
                         'units': 'degrees_east'},
                 'Alt_Grid': {'units': 'km'},
                 'wavelength': {'units': 'nm',
                                'description': 'wavelength at which aerosol extinction is retrieved'},
                 'O3': {'standard_name': 'number_concentration_of_ozone_molecules_in_air',
                        'units': 'cm-3'},
                 'NO2': {'standard_name': 'number_concentration_of_nitrogen_dioxide_molecules_in_air',
                         'units': 'cm-3'},
                 'H2O': {'standard_name': 'number_concentration_of_water_vapor_in_air',
                         'units': 'cm-3'},
                 'Ext': {'standard_name': 'volume_extinction_coefficient_in_air_due_to_ambient_aerosol_particles',
                         'units': 'km-1'},
                 'O3_Err': {'standard_name': 'number_concentration_of_ozone_molecules_in_air_error',
                            'units': 'percent'},
                 'NO2_Err': {'standard_name': 'number_concentration_of_nitrogen_dioxide_molecules_in_air_error',
                             'units': 'percent'},
                 'H2O_Err': {'standard_name': 'number_concentration_of_water_vapor_in_air_error',
                             'units': 'percent'},
                 'Ext_Err': {'standard_name': 'volume_extinction_coefficient_in_air_due_to_ambient_aerosol_'
                                              'particles_error',
                             'units': 'percent'},
                 'Duration': {'units': 'seconds',
                              'description': 'duration of the sunrise/sunset event'},
                 'Beta': {'units': 'degrees',
                          'description': 'angle between the satellite orbit plane and the sun'},
                 'Trop_Height': {'units': 'km'},
                 'Radius': {'units': 'microns'},
                 'SurfDen': {'units': 'microns2 cm-3'}}

        for key in attrs.keys():
            data[key].attrs = attrs[key]

        git_repo = 'https://github.com/LandonRieger/pySAGE.git'
        data.attrs = {'description': 'Retrieved vertical profiles of  aerosol extinction, ozone, '
                                     'nitrogen dioxide, water vapor, and meteorological profiles from SAGE II '
                                     'version 7.00',
                      'publication reference': 'Damadeo, R. P., Zawodny, J. M., Thomason, L. W., & Iyer, N. (2013). '
                                               'SAGE version 7.0 algorithm: application to SAGE II. Atmospheric '
                                               'Measurement Techniques, 6(12), 3539-3561.',
                      'title': 'SAGE II version 7.00',
                      'date_created': pd.Timestamp.now().strftime('%B %d %Y'),
                      'source_code': 'repository: ' + git_repo + ' revision: ' + pysagereader.__version__,
                      'source_data': 'https://eosweb.larc.nasa.gov/project/sage2/sage2_v7_table',
                      'version': pysagereader.__version__,
                      'Conventions': 'CF-1.7'}

        if self.cf_names:
            names = {'Lat': 'latitude',
                     'Lon': 'longitude',
                     'Alt_Grid': 'altitude',
                     'Beta': 'beta_angle',
                     'Ext': 'aerosol_extinction',
                     'Ext_Err': 'aerosol_extinction_error',
                     'O3': 'ozone',
                     'O3_Err': 'ozone_error',
                     'NO2': 'no2',
                     'NO2_Err': 'no2_error',
                     'SurfDen': 'surface_area_density',
                     'SurfDen_Err': 'surface_area_density_error',
                     'radius': 'effective_radius',
                     'radius_err': 'effective_radius_error',
                     'Density': 'air_density',
                     'Density_Err': 'air_density_error',
                     'Type_Sat': 'satellite_sunset',
                     'Type_Tan': 'local_sunset',
                     'Trop_Height': 'tropopause_altitude',
                     'Duration': 'event_duration'}

            for key in names.keys():
                try:
                    data.rename({key: names[key]}, inplace=True)
                except ValueError:
                    pass

        return data

    @staticmethod
    def convert_index_bit_flags(data: Dict) -> xr.Dataset:
        """
        Convert the int32 index flags to a dataset of distinct flags

        Parameters
        ----------
        data
            Dictionary of input data as returned by ``load_data``

        Returns
        -------
            Dataset of the index bit flags
        """
        flags = dict()
        flags['pmc_present'] = 0
        flags['h2o_zero_found'] = 1
        flags['h2o_slow_convergence'] = 2
        flags['h2o_ega_failure'] = 3
        flags['default_nmc_temp_errors'] = 4
        flags['ch2_aero_model_A'] = 5
        flags['ch2_aero_model_B'] = 6
        flags['ch2_new_wavelength'] = 7
        flags['incomplete_nmc_data'] = 8
        flags['mirror_model'] = 15
        flags['twomey_non_conv_rayleigh'] = 19
        flags['twomey_non_conv_386_Aero'] = 20
        flags['twomey_non_conv_452_Aero'] = 21
        flags['twomey_non_conv_525_Aero'] = 22
        flags['twomey_non_conv_1020_Aero'] = 23
        flags['twomey_non_conv_NO2'] = 24
        flags['twomey_non_conv_ozone'] = 25
        flags['no_shock_correction'] = 30

        f = dict()
        for key in flags.keys():
            f[key] = (data['InfVec'] & 2 ** flags[key]) > 0

        xr_data = []
        time = pd.to_timedelta(data['mjd'], 'D') + pd.Timestamp('1858-11-17')
        for key in f.keys():
            xr_data.append(xr.DataArray(f[key], coords=[time], dims=['time'], name=key))

        return xr.merge(xr_data)

    @staticmethod
    def convert_species_bit_flags(data: Dict) -> xr.Dataset:
        """
        Convert the int32 species flags to a dataset of distinct flags

        Parameters
        ----------
        data
            Dictionary of input data as returned by `load_data`

        Returns
        -------
            Dataset of the index bit flags
        """
        flags = dict()
        flags['separation_method'] = [0, 1, 2]
        flags['one_chan_aerosol_corr'] = 3
        flags['no_935_aerosol_corr'] = 4
        flags['Large_1020_OD'] = 5
        flags['NO2_Extrap'] = 6
        flags['Water_vapor_ratio'] = [7, 8, 9, 10]
        flags['Cloud_Bit_1'] = 11
        flags['Cloud_Bit_2'] = 12
        flags['No_H2O_Corr'] = 13
        flags['In_Troposphere'] = 14

        separation_method = dict()
        separation_method['no_aerosol_method'] = 0
        separation_method['trans_no_aero_to_five_chan'] = 1
        separation_method['standard_method'] = 2
        separation_method['trans_five_chan_to_low'] = 3
        separation_method['four_chan_method'] = 4
        separation_method['trans_four_chan_to_three_chan'] = 5
        separation_method['three_chan_method'] = 6
        separation_method['extension_method'] = 7

        f = dict()
        for key in flags.keys():
            if hasattr(flags[key], '__len__'):
                if key == 'separation_method':
                    for k in separation_method.keys():
                        temp = data['ProfileInfVec'] & np.sum([2 ** k for k in flags[key]])
                        f[k] = temp == separation_method[k]
                else:
                    temp = data['ProfileInfVec'] & np.sum([2 ** k for k in flags[key]])
                    f[key] = temp >> flags[key][0]  # shift flag to save only significant bits
            else:
                f[key] = (data['ProfileInfVec'] & 2 ** flags[key]) > 0

        xr_data = []
        time = pd.to_timedelta(data['mjd'], 'D') + pd.Timestamp('1858-11-17')
        for key in f.keys():
            xr_data.append(xr.DataArray(f[key], coords=[time, data['Alt_Grid'][0:140]], dims=['time', 'Alt_Grid'],
                                        name=key))

        return xr.merge(xr_data)
