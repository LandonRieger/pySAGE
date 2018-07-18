import warnings

import matplotlib.pyplot as plt
import numpy as np
from astropy.time import Time

from pysagereader.sage_iii_reader import SAGEIIILoaderV400
from pysagereader.sage_ii_reader import SAGEIILoaderV700


def sage_ii_ozone_time_series( data_folder ):
    """
    Basic example of using the loader to plot the monthly averaged ozone in the tropics
    """

    #load the data
    sage = SAGEIILoaderV700(output_format='xarray')
    sage.data_folder = data_folder
    data = sage.load_data('2004-10-19','2005-7-1', -10,10)

    #setup the time bins
    time_res = 30
    mjds = np.arange(np.min(data['mjd']), np.max(data['mjd']), time_res)

    #get rid of bad data
    data['O3'][data['O3'] == data['FillVal']] = np.nan
    data['O3'][data['O3_Err']>10000]       = np.nan

    #get ozone altitudes
    o3_alts = data['Alt_Grid'][(data['Alt_Grid'] >= data['Range_O3'][0]) & (data['Alt_Grid'] <= data['Range_O3'][1])]

    # average the ozone profiles
    o3 = np.zeros((len(o3_alts), len(mjds)))
    for idx, mjd in enumerate(mjds):
        good = (data['mjd'] > mjd) & (data['mjd'] < mjd + time_res)
        with warnings.catch_warnings():  # there will be all nans at high/low altitudes, its fine
            warnings.simplefilter("ignore", category=RuntimeWarning)
            o3[:, idx] = np.nanmean(data['O3'][good, :], axis=0)

    plot_data(o3_alts, mjds + time_res/2, o3 )

def sage_iii_ozone_time_series( data_folder ):
    """
    Basic example of using the loader to plot the monthly averaged ozone in the tropics
    """

    # load the data
    sage = SAGEIIILoaderV400()
    sage.data_folder = data_folder
    data = sage.load_data('2003-12-24','2006-7-1', -90,90)

    # setup the time bins
    time_res = 7
    mjds = np.arange(np.min(data['mjd']), np.max(data['mjd']), time_res)

    # get rid of bad data
    data['O3'][data['O3'] == data['FillVal']] = np.nan
    # data['O3'][data['O3_Err'] > 10000] = np.nan

    # get ozone altitudes
    o3_alts = data['Alt_Grid'][(data['Alt_Grid'] >= data['Range_O3'][0]) & (data['Alt_Grid'] <= data['Range_O3'][1])]

    # average the ozone profiles
    o3 = np.zeros((len(o3_alts), len(mjds)))
    for idx, mjd in enumerate(mjds):
        good = (data['mjd'] > mjd) & (data['mjd'] < mjd + time_res)
        with warnings.catch_warnings():  # there will be all nans at high/low altitudes, its fine
            warnings.simplefilter("ignore", category=RuntimeWarning)
            o3[:, idx] = np.nanmean(data['O3'][good, :], axis=0)

    # make the plot
    plot_data(o3_alts,mjds + time_res/2,o3)

def plot_data(alts,mjds,val):

    #make the plot
    plt.contourf(Time(mjds, format='mjd').datetime, alts, val, levels=np.arange(0,7e12,1e11),extend='both')
    plt.colorbar()
    plt.clim(0,7e12)
    plt.ylabel('Altitude [km]')
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=45)
    plt.ylim(15,50)

if __name__ == "__main__":
    sage_ii_ozone_time_series(r'C:\Users\lando\Desktop\Sage2_v7.00')