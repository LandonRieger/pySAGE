import numpy as np
import os
from struct import unpack
from collections import OrderedDict
from astropy.time import Time
import h5py
import copy


class SAGEIIIDataLoaderV400(object):

    def __init__(self):

        self.data_folder = ''
        self.version = 'v04.00'
        self.data_file = ''
        self.xml_file = '.xml'
        self.data_format = self.get_data_format()

        self.fill_value = np.nan


    def get_data_format(self):

        data_format = OrderedDict()

        data_format['Event Identification Tag']             = (0,4,1,'int32')
        data_format['Year-Day Tag']                         = (4,8,1,'int32')
        data_format['Instrument Elapsed Time in Orbit']     = (8,12,1,'int32')
        data_format['Fill Value Int']                       = (12,16,1,'int32')
        data_format['Fill Value Float']                     = (16,20,1,'float32')
        data_format['Mission Identification']               = (20,24,1,'int32')

        data_format['Version: Definitive Orbit Processing'] = (24,28,1,'float32')
        data_format['Version: Level 0 Processing']          = (28,32,1,'float32')
        data_format['Version: Software Processing']         = (32,36,1,'float32')
        data_format['Version: Data Product']                = (36,40,1,'float32')
        data_format['Version: Spectroscopy']                = (40,44,1,'float32')
        data_format['Version: GRAM 95']                     = (44,48,1,'float32')
        data_format['Version: Meteorlogical']               = (48,52,1,'float32')

        data_format['Altitude–Based Grid Spacing']          = (52,56,1,'float32')
        data_format['Number of Altitude–Based Array Values']= (56,60,1,'int32')
        data_format['Number of Aerosol Channels']           = (60,64,1,'int32')
        data_format['Number of Ground Track Values']        = (64,68,1,'int32')
        data_format['Number of Aerosol Extinction Altitude Levels']= (68,72,1,'int32')

        data_format['Spacecraft–Referenced Event Type']     = (72,76,1,'int32')
        data_format['Earth–Referenced Event Type']          = (76,80,1,'int32')
        data_format['Event Beta Angle']                     = (80,84,1,'float32')
        data_format['Event Status Bit Flags']               = (84,88,1,'int32')

        data_format['Data Capture Start Date']              = (88,92,1,'int32')
        data_format['Data Capture Start Time']              = (92,96,1,'int32')
        data_format['Subtangent Start Latitude']            = (96,100,1,'float32')
        data_format['Subtangent Start Longitude']           = (100,104,1,'float32')
        data_format['Subtangent Start Altitude']            = (104,108,1,'float32')

        data_format['Data Capture End Date']                = (108,112,1,'int32')
        data_format['Data Capture End Time']                = (112,116,1,'int32')
        data_format['Subtangent End Latitude']              = (116,120,1,'float32')
        data_format['Subtangent End Longitude']             = (120,124,1,'float32')
        data_format['Subtangent End Altitude']              = (124,128,1,'float32')

        data_format['Date']                                 = (128,172,1,'int32')
        data_format['Time']                                 = (172,216,1,'int32')
        data_format['Subtangent Latitude']                  = (216, 260, 1, 'float32')
        data_format['Subtangent Longitude']                 = (260, 304, 1, 'float32')
        data_format['Subtangent Altitude']                  = (304, 348, 1, 'float32')

        data_format['Homogeneity Flags']                    = (348, 1148, 1, 'int32')
        data_format['Geometric Altitude']                   = (1148, 1948, 1, 'float32')
        data_format['Geopotential Altitude']                = (1948, 2748, 1, 'float32')

        data_format['Temperature']                          = (2748, 3548, 1, 'float32')
        data_format['Temperature Uncertainty']              = (3548, 4348, 1, 'float32')
        data_format['Pressure']                             = (4348, 5148, 1, 'float32')
        data_format['Pressure Uncertainty']                 = (5148, 5948, 1, 'float32')
        data_format['Pressure/Temperature Array Source Flags']             = (5948, 6748, 1, 'int32')

        data_format['Tropopause Temperature']               = (6748, 6752, 1, 'float32')
        data_format['Tropopause Geometric Altitude']        = (6752, 6756, 1, 'float32')

        data_format['Composite Ozone Concentration']                  = (6756, 7556, 1, 'float32')
        data_format['Composite Ozone Concentration Uncertainty']      = (7556, 8356, 1, 'float32')
        data_format['Composite Ozone Slant Path Column Density']      = (8356, 9156, 1, 'float32')
        data_format['Composite Ozone Slant Path Column Density Uncertainty'] = (9156, 9956, 1, 'float32')
        data_format['Composite Ozone QA Bit Flags ']                = (9956, 10756, 1, 'int32')

        data_format['Mesospheric Ozone Concentration']              = (10756, 11556, 1, 'float32')
        data_format['Mesospheric Ozone Concentration Uncertainty']  = (11556, 12356, 1, 'float32')
        data_format['Mesospheric Ozone Slant Path Column Density']  = (12356, 13156, 1, 'float32')
        data_format['Mesospheric Ozone Slant Path Column Density Uncertainty'] = (13156, 13956, 1, 'float32')
        data_format['Mesospheric Ozone QA Bit Flags ']              = (13956, 14756, 1, 'int32')

        data_format['MLR Ozone Concentration']                      = (14756, 15556, 1, 'float32')
        data_format['MLR Ozone Concentration Uncertainty']          = (15556, 16356, 1, 'float32')
        data_format['MLR Ozone Slant Path Column Density']          = (16356, 17156, 1, 'float32')
        data_format['MLR Ozone Slant Path Column Density Uncertainty'] = (17156, 17956, 1, 'float32')
        data_format['MLR Ozone QA Bit Flags ']                      = (17956, 18756, 1, 'int32')

        data_format['LSQ Ozone Concentration']                      = (18756, 19556, 1, 'float32')
        data_format['LSQ Ozone Concentration Uncertainty']          = (19556, 20356, 1, 'float32')
        data_format['LSQ Ozone Slant Path Column Density']          = (20356, 21156, 1, 'float32')
        data_format['LSQ Ozone Slant Path Column Density Uncertainty'] = (21156, 21956, 1, 'float32')
        data_format['LSQ Ozone QA Bit Flags ']                      = (21956, 22756, 1, 'int32')

        data_format['Water Vapor Concentration']                    = (22756, 23556, 1, 'float32')
        data_format['Water Vapor Concentration Uncertainty']        = (23556, 24356, 1, 'float32')
        data_format['Water Vapor QA Bit Flags']                     = (24356, 25156, 1, 'int32')

        data_format['NO2 Concentration']                            = (25156, 25956, 1, 'float32')
        data_format['NO2 Concentration Uncertainty']                = (25956, 26756, 1, 'float32')
        data_format['NO2 Slant Path Column Density']                = (26756, 27556, 1, 'float32')
        data_format['NO2 Slant Path Column Density Uncertainty']    = (27556, 28356, 1, 'float32')
        data_format['NO2 QA Bit Flags ']                            = (28356, 29156, 1, 'int32')

        data_format['Retrieved Temperature']                        = (29156, 29956, 1, 'float32')
        data_format['Retrieved Temperature Uncertainty']            = (29956, 30756, 1, 'float32')
        data_format['Retrieved Pressure']                           = (30756, 31556, 1, 'float32')
        data_format['Retrieved Pressure Uncertainty']               = (31556, 32356, 1, 'float32')
        data_format['Retrieved Pressure/Temperature QA Bit Flags']  = (32356, 33156, 1, 'int32')

        data_format['Aerosol Wavelengths']                          = (33156, 33192, 1, 'float32')
        data_format['Half–Bandwidths of Aerosol Channels']          = (33192, 33228, 1, 'float32')
        data_format['Stratospheric Optical Depth']                  = (33228, 33264, 1, 'float32')
        data_format['Stratospheric Optical Depth Uncertainty']      = (33264, 33300, 1, 'float32')
        data_format['Stratospheric Optical Depth QA Bit Flags']     = (33300, 33336, 1, 'int32')

        data_format['Aerosol Extinction Channel 1']                 = (33336, 33696, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 1']     = (33696, 34056, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 1']    = (34056, 34416, 1, 'int32')

        data_format['Aerosol Extinction Channel 2']                 = (34416, 34776, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 2']     = (34776, 35136, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 2']    = (35136, 35496, 1, 'int32')

        data_format['Aerosol Extinction Channel 3']                 = (35496, 35856, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 3']     = (35856, 36216, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 3']    = (36216, 36576, 1, 'int32')

        data_format['Aerosol Extinction Channel 4']                 = (36576, 36936, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 4']     = (36936, 37296, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 4']    = (37296, 37656, 1, 'int32')

        data_format['Aerosol Extinction Channel 5']                 = (37656, 38016, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 5']     = (38016, 38376, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 5']    = (38376, 38736, 1, 'int32')

        data_format['Aerosol Extinction Channel 6']                 = (38736, 39096, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 6']     = (39096, 39456, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 6']    = (39456, 39816, 1, 'int32')

        data_format['Aerosol Extinction Channel 7']                 = (39816, 40176, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 7']     = (40176, 40536, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 7']    = (40536, 34416, 1, 'int32')

        data_format['Aerosol Extinction Channel 8']                 = (40896, 41256, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 8']     = (41256, 41616, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 8']    = (41616, 34416, 1, 'int32')

        data_format['Aerosol Extinction Channel 9']                 = (41976, 42336, 1, 'float32')
        data_format['Aerosol Extinction Uncertainty Channel 9']     = (42336, 42696, 1, 'float32')
        data_format['Aerosol Extinction QA Bit Flags Channel 9']    = (42696, 43056, 1, 'int32')

        data_format['Aerosol Spectral Dependence Flag']             = (43056, 43416, 1, 'float32')
        data_format['1020nm/Rayleigh Extinction Ratio']             = (43416, 43776, 1, 'float32')
        data_format['1020nm/Rayleigh Extinction Ratio Uncertainty'] = (43776, 44136, 1, 'float32')
        data_format['1020nm/Rayleigh Extinction Ratio QA Bit Flags']= (44136, 44495, 1, 'int32')

        return data_format

    def load_file(self,file):

        # load the file into the buffer
        file_format = self.data_format
        with open(file, "rb") as f:
            buffer = f.read()

        # load the data from the buffer
        data = dict()
        for key in self.data_format.keys():
            dt = np.dtype(file_format[key][3])
            dt = dt.newbyteorder('>')
            try:
                data[key] = copy.copy(np.frombuffer(buffer[file_format[key][0]:file_format[key][1]], dtype=dt))
            except:
                print(key)

        return data

if __name__ == '__main__':

    s = SAGEIIIDataLoaderV400()
    s.load_file()
