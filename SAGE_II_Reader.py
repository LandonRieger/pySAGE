import numpy as np
import os
from collections import OrderedDict
from astropy.time import Time
import copy

class SAGEIILoaderV700(object):
    """
    Class designed to load the v7.00 SAGE II spec and index files provided by NASA ADSC into python

    Data files must be accessible by the users machine, and can be downloaded from:
    https://eosweb.larc.nasa.gov/project/sage2/sage2_v7_table

    :example
    sage = SAGEIILoaderV700()
    sage.data_folder = 'path/to/data'
    data = sage.load_data('2004-1-1','2004-5-1')

    In addition to the sage ii fields reported in the files, two additional time fields are provided
    to allow for easier subsetting of the data.

    data['mjd'] is a numpy array containing the modified julian dates of each scan
    date['time'] is an astropy.time object containing the times of each scan
    """
    def __init__(self):

        self.data_folder  = ''
        self.version      = '7.00'
        self.index_file   = 'SAGE_II_INDEX_'
        self.spec_file    = 'SAGE_II_SPEC_'

        self.fill_value   = np.nan

        self.spec_format  = self.get_spec_format()
        self.index_format = self.get_index_format()

    @staticmethod
    def get_spec_format():
        """
        spec format taken from sg2_specinfo.pro provided in the v7.00 download

        used for reading the binary data format

        :return
        spec (Ordered Dictionary)
        an ordered dictionary of variables provided in the spec file. Each dictionary
        field contains a tuple with the information (data type, number of data points, data type length in bytes). Ordering is
        important as the sage ii binary files are read sequentially.
        """
        spec = OrderedDict()
        spec['Tan_Alt'] = ('float32',8,4)       # Subtangent Altitudes(km)
        spec['Tan_Lat'] = ('float32',8,4)       # Subtangent Latitudes @ Tan_Alt(deg)
        spec['Tan_Lon'] = ('float32',8,4)       # Subtangent Longitudes @ Tan_Alt(deg)

        spec['NMC_Pres'] = ('float32',140,4)    # Gridded Pressure profile(mb)
        spec['NMC_Temp'] = ('float32',140,4)    # Gridded Temperature profile(K)
        spec['NMC_Dens'] = ('float32',140,4)    # Gridded Density profile(cm ^ (-3))
        spec['NMC_Dens_Err'] = ('int16',140,2)  # Error in NMC_Dens( % * 1000)

        spec['Trop_Height'] = ('float32',1,4)   # NMC Tropopause Height(km)
        spec['Wavelength'] = ('float32',7,4)    # Wavelength of each channel(nm)

        spec['O3'] = ('float32',140,4)          # O3 Density profile 0 - 70 Km(cm ^ (-3))
        spec['NO2'] = ('float32',100,4)         # NO2 Density profile 0 - 50 Km(cm ^ (-3))
        spec['H2O'] = ('float32',100,4)         # H2O Volume Mixing Ratio 0 - 50 Km(ppp)

        spec['Ext386'] = ('float32',80,4)       # 386 nm Extinction 0 - 40 Km(1 / km)
        spec['Ext452'] = ('float32',80,4)       # 452 nm Extinction 0 - 40 Km(1 / km)
        spec['Ext525'] = ('float32',80,4)       # 525 nm Extinction 0 - 40 Km(1 / km)
        spec['Ext1020'] = ('float32',80,4)      # 1020 nm Extinction 0 - 40 Km(1 / km)
        spec['Density'] = ('float32',140,4)     # Calculated Density 0 - 70 Km(cm ^ (-3))
        spec['SurfDen'] = ('float32',80,4)      # Aerosol surface area dens 0 - 40 km(um ^ 2 / cm ^ 3)
        spec['Radius'] = ('float32',80,4)       # Aerosol effective radius 0 - 40 km(um)

        spec['Dens_Mid_Atm'] = ('float32',70,4) # Middle Atmosphere Density(cm ^ (-3))
        spec['O3_Err'] = ('int16',140,2)        # Error in O3 density profile( % * 100)
        spec['NO2_Err'] = ('int16',100,2)       # Error in NO2 density profile( % * 100)
        spec['H2O_Err'] = ('int16',100,2)       # Error in H2O mixing ratio( % * 100)

        spec['Ext386_Err'] = ('int16',80,2)     # Error in 386 nm Extinction( % * 100)
        spec['Ext452_Err'] = ('int16',80,2)     # Error in 452 nm Extinction( % * 100)
        spec['Ext525_Err'] = ('int16',80,2)     # Error in 525 nm Extinction( % * 100)
        spec['Ext1020_Err'] = ('int16',80,2)    # Error in 1019 nm Extinction( % * 100)
        spec['Density_Err'] = ('int16',140,2)   # Error in Density( % * 100)
        spec['SurfDen_Err'] = ('int16',80,2)    # Error in surface area dens( % * 100)
        spec['Radius_Err'] = ('int16',80,2)     # Error in aerosol radius( % * 100)

        spec['Dens_Mid_Atm_Err'] = ('int16',70,2) # Error in Middle Atm.Density( % * 100)
        spec['InfVec'] = ('uint16',140,2)       # Informational Bit flags

        return spec

    @staticmethod
    def get_index_format():
        """
        index format taken from sg2_indexinfo.pro provided in the v7.00 download

        used for reading the binary data format

        :return
        info (dictionary)
        an ordered dictionary of variables provided in the index file. Each dictionary
        field contains a tuple with the information (data type, length). Ordering is
        important as the sage ii binary files are read sequentially.
        """

        info = OrderedDict()
        
        info['num_prof']        = ('uint32',1,4)  # Number of profiles in these files
        info['Met_Rev_Date']    = ('uint32',1,4)  # LaRC Met Model Revision Date(YYYYMMDD)
        info['Driver_Rev']      = ('char',8,1)    # LaRC Driver Version(e.g. 6.20)
        info['Trans_Rev']       = ('char',8,1)    # LaRC Transmission Version
        info['Inv_Rev']         = ('char',8,1)    # LaRC Inversion Version
        info['Spec_Rev']        = ('char',8,1)    # LaRC Inversion Version
        info['Eph_File_Name']   = ('char',32,1)   # Ephemeris data file name
        info['Met_File_Name']   = ('char',32,1)   # Meteorological data file name
        info['Ref_File_Name']   = ('char',32,1)   # Refraction data file name
        info['Tran_File_Name']  = ('char',32,1)   # Transmission data file name
        info['Spec_File_Name']  = ('char',32,1)   # Species profile file name
        info['FillVal']         = ('float32',1,4) # Fill value

        # Altitude grid and range info
        info['Grid_Size']        = ('float32',1,4)   # Altitude grid spacing(0.5 km)
        info['Alt_Grid']         = ('float32',200,4) # Geometric altitudes(0.5, 1.0, ..., 100.0 km)
        info['Alt_Mid_Atm']      = ('float32',70,4)  # Middle atmosphere geometric altitudes
        info['Range_Trans']      = ('float32',2,4)   # Transmission min & max altitudes[0.5, 100.]
        info['Range_O3']         = ('float32',2,4)   # Ozone min & max altitudes[0.5, 70.0]
        info['Range_NO2']        = ('float32',2,4)   # NO2 min & max altitudes[0.5, 50.0]
        info['Range_H2O']        = ('float32',2,4)   # Water vapor min & max altitudes[0.5, 50.0]
        info['Range_Ext']        = ('float32',2,4)   # Aerosol extinction min & max altitudes[0.5, 40.0]
        info['Range_Dens']       = ('float32',2,4)   # Density min & max altitudes[0.5, 70.0]
        info['Spare']            = ('float32',2,4)   #

        # Event specific info useful for data subsetting
        info['YYYYMMDD']         = ('int32',930,4)   # Event date at 20km subtangent point
        info['Event_Num']        = ('int32',930,4)   # Event number
        info['HHMMSS']           = ('int32',930,4)   # Event time at 20km
        info['Day_Frac']         = ('float32',930,4) # Time of year(DDD.frac) at 20 km
        info['Lat']              = ('float32',930,4) # Subtangent latitude at 20 km(-90, +90)
        info['Lon']              = ('float32',930,4) # Subtangent longitude at 20 km(-180, +180)
        info['Beta']             = ('float32',930,4) # Spacecraft beta angle(deg)
        info['Duration']         = ('float32',930,4) # Duration of event(sec)
        info['Type_Sat']         = ('int16',930,2)   # Event Type Instrument(0 = SR, 1 = SS)
        info['Type_Tan']         = ('int16',930,2)   # Event Type Local(0 = SR, 1 = SS)

        # Process tracking and flag info
        info['Dropped']          = ('int32',930,4)   # Dropped event flag
        info['InfVec']           = ('uint32',930,4)  # Bit flags relating to processing

        # Record creation dates and times
        info['Eph_Cre_Date']     = ('int32',930,4)  # Record creation date(YYYYMMDD format)
        info['Eph_Cre_Time']     = ('int32',930,4)  # Record creation time(HHMMSS format)
        info['Met_Cre_Date']     = ('int32',930,4)  # Record creation date(YYYYMMDD format)
        info['Met_Cre_Time']     = ('int32',930,4)  # Record creation time(HHMMSS format)
        info['Ref_Cre_Date']     = ('int32',930,4)  # Record creation date(YYYYMMDD format)
        info['Ref_Cre_Time']     = ('int32',930,4)  # Record creation time(HHMMSS format)
        info['Tran_Cre_Date']    = ('int32',930,4)  # Record creation date(YYYYMMDD format)
        info['Tran_Cre_Time']    = ('int32',930,4)  # Record creation time(HHMMSS format)
        info['Spec_Cre_Date']    = ('int32',930,4)  # Record creation date(YYYYMMDD format)
        info['Spec_Cre_Time']    = ('int32',930,4)  # Record creation time(HHMMSS format)

        return info

    def get_spec_filename(self, year, month):
        """
        Returns the spec filename given a year and month

        :param year: (int)
        year of the data that will be loaded
        :param month: (int)
        month of the data that will be loaded
        :return:
        filename of the spec file where the data is stored
        """
        file = os.path.join(self.data_folder,
                            self.spec_file + str(int(year)) + str(int(month)).zfill(2) + '.' + self.version)

        if not os.path.isfile(file):
            file = None

        return file

    def get_index_filename(self, year, month):
        """
        Returns the index filename given a year and month

        :param year: (int)
        year of the data that will be loaded
        :param month: (int)
        month of the data that will be loaded
        :return:
        filename of the index file where the data is stored
        """

        file = os.path.join(self.data_folder,
                     self.index_file + str(int(year)) + str(int(month)).zfill(2) + '.' + self.version)

        if not os.path.isfile(file):
            file = None

        return file

    def read_spec_file(self, file, num_profiles):
        """

        :param file: (str)
        name of the spec file to be read
        :param num_profiles: (int)
        number of profiles to read from the spec file (usually determined from the index file)
        :return: list
        list of dictionaries containing the spec data. Each list is one event
        """

        #load the file into the buffer
        file_format = self.spec_format
        with open(file, "rb") as f:
            buffer = f.read()

        #initialize the list of dictionaries
        data = [None] * num_profiles
        for p in range(num_profiles):
            data[p] = dict()

        # load the data from the buffer
        bidx = 0
        for p in range(num_profiles):
            for key in file_format.keys():
                data[p][key]=copy.copy(np.frombuffer(buffer[bidx:bidx+file_format[key][2]*file_format[key][1]],dtype=file_format[key][0]))
                bidx += file_format[key][2]*file_format[key][1]

        return data

    def read_index_file(self, file):
        """
        Read the binary file into a python data structure

        :param file: (str)
        filename to be read
        :return: data: (dictionary)
        contains the data from the file
        """

        file_format = self.index_format
        with open(file, "rb") as f:
            buffer = f.read()

        data = dict()

        #load the data from file into a list
        bidx = 0
        for key in file_format.keys():
            if file_format[key][0] == 'char':
                data[key] = copy.copy(buffer[bidx:bidx + file_format[key][2] * file_format[key][1]].decode('utf-8'))
            else:
                data[key] = copy.copy(np.frombuffer(buffer[bidx:bidx + file_format[key][2] * file_format[key][1]],dtype=file_format[key][0]))
                if len(data[key]) == 1:
                    data[key] = data[key][0]
            bidx += file_format[key][2] * file_format[key][1]

        #make a more useable time field
        date_str = []
        #If the time overflows by less than the scan time just set it to midnight
        data['HHMMSS'][(data['HHMMSS']>=240000) & (data['HHMMSS']<(240000 + data['Duration']))] = 235959
        #otherwise, set it as invalid
        data['HHMMSS'][data['HHMMSS'] >= 240000] = -999
        for idx,(ymd, hms) in enumerate(zip(data['YYYYMMDD'], data['HHMMSS'])):
            if (ymd < 0) | (hms < 0):
                date_str.append('1970-1-1 00:00:00')    #invalid sage ii date
            else:
                hours = int(hms/10000)
                mins  = int( (hms % 10000)/100 )
                secs  = hms % 100
                date_str.append(str(ymd)[0:4] + '-' + str(ymd)[4:6].zfill(2) + '-' + \
                        str(ymd)[6::].zfill(2) + ' ' + str(hours).zfill(2) + ':' + \
                        str(mins).zfill(2) + ':' + str(secs).zfill(2))

        data['time'] = Time(date_str,format='iso')
        data['mjd']  = data['time'].mjd
        data['mjd'][data['mjd'] < 40588] = -999 #get rid of invalid dates

        return data

    def load_data(self, min_date, max_date, min_lat=-90, max_lat=90, min_lon=-180, max_lon=360):
        """
        Load the SAGE II data for the specified dates and locations.

        :param min_date: (str)
        start date where data will be loaded in iso format, eg: '2004-1-1'
        :param max_date: (str)
        end date where data will be loaded in iso format, eg: '2004-1-1'
        :param min_lat: (optional, float)
        minimum latitude
        :param max_lat: (optional, float)
        maximum latitude
        :param min_lon: (optional, float)
        minimum longitude
        :param max_lon: (optional, float)
        maximum longitude
        :return:
        data (dict)
        Variables are returned as numpy arrays (1 or 2 dimensional depending on the variable)
        """
        min_time = Time(min_date,format='iso')
        max_time = Time(max_date,format='iso')

        data = dict()
        init = False

        #create a list of unique year/month combinations between the start/end dates
        uniq = OrderedDict()
        for year in [(t.datetime.year,t.datetime.month) for t in Time(np.arange(min_time.mjd,max_time.mjd,27),format='mjd')]:
            uniq[year] = year

        #load in the data from the desired months
        for (year,month) in list(uniq.values()):

            print('loading data for : ' + str(year) + '/' + str(month))
            indx_file = self.get_index_filename(year, month)

            #if the file does not exist move on to the next month
            if indx_file is None:
                continue

            indx_data = self.read_index_file(indx_file)
            numprof = indx_data['num_prof']
            spec_data = self.read_spec_file(self.get_spec_filename(year,  month), numprof )

            #get rid of the duplicate names for InfVec
            for sp in spec_data:
                sp['ProfileInfVec'] = copy.copy(sp['InfVec'])
                del sp['InfVec']


            for key in indx_data.keys():
                # get rid of extraneous profiles in the index so index and spec are the same lengths
                if hasattr(indx_data[key], '__len__'):
                    indx_data[key] = np.delete(indx_data[key], np.arange(numprof,930))

                #add the index values to the data set
                if key in data.keys():
                    # we dont want to replicate certain fields
                    if (key[0:3] != 'Alt') & (key[0:5] != 'Range') & (key[0:7] != 'FillVal'):
                        data[key] = np.append(data[key],indx_data[key])
                else:
                    if key == 'FillVal':
                        data[key] = indx_data[key]
                    else:
                        data[key] = [indx_data[key]]

            #initialize the data dictionaries as lists
            if init is False:
                for key in spec_data[0].keys():
                    data[key] = []
                init = True

            # add the spec values to the data set
            for key in spec_data[0].keys():
                data[key].append(np.asarray([sp[key] for sp in spec_data]))

        #join all of our lists into an array - this could be done more elegantly with vstack to avoid
        # the temporary lists, but this is much faster
        for key in data.keys():
            if key == 'FillVal':
                data[key] = float(data[key]) #make this a simple float rather than zero dimensional array
            elif len(data[key][0].shape) > 0:
                data[key] = np.concatenate(data[key],axis=0)
            else:
                data[key] = np.asarray(data[key])

        data = self.subset_data(data, min_date, max_date, min_lat, max_lat, min_lon, max_lon)
        return data

    @staticmethod
    def subset_data(data, min_date, max_date, min_lat, max_lat, min_lon, max_lon):
        """
        Removes any data from the dictionary that does not meet the specified time, latitude and longitude requirements.

        :param data: (dictionary)
        dictionary of sage ii data. Must have the fields 'mjd', 'Lat' and 'Lon'. All others are optional
        :param min_date: (str)
        start date in iso format
        :param max_date: (str)
        end date in iso format
        :param min_lat: (float)
        minimum latitude
        :param max_lat: (float)
        maximum latitude
        :param min_lon: (float)
        minimum longitude
        :param max_lon: (float)
        maximum longitude
        :return:
        returns the dictionary with only data in the valid latitude, longitude and time range
        """
        min_mjd = Time(min_date, format='iso').mjd
        max_mjd = Time(max_date, format='iso').mjd

        good = (data['mjd'] > min_mjd) & (data['mjd'] < max_mjd) & \
               (data['Lat'] > min_lat) & (data['Lat'] < max_lat) & \
               (data['Lon'] > min_lon) & (data['Lon'] < max_lon)

        if np.any(good):
            for key in data.keys():
                if hasattr(data[key],'__len__'):
                    if data[key].shape[0] == len(good):
                        data[key] = data[key][good]
        else:
            print('no data satisfies the criteria')

        return data