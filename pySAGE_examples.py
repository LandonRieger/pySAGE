from SAGE_II_Reader import SAGEIILoaderV700
from astropy.time import Time
import matplotlib.pyplot as plt
import numpy as np
import warnings

def ozone_time_series( data_folder ):
    """
    Basic example of using the loader to plot the monthly averaged ozone in the tropics
    """

    #load the data
    sage = SAGEIILoaderV700()
    sage.data_folder = data_folder
    data = sage.load_data('1985-6-1','2006-6-1', -10,10)

    #setup the time bins
    time_res = 30
    mjds = np.arange(np.min(data['mjd']), np.max(data['mjd']), time_res)

    #get rid of bad data
    data['O3'][data['O3'] == data['FillVal']] = np.nan
    data['O3'][data['O3_Err']>10000]       = np.nan

    #get ozone altitudes
    o3_alts = data['Alt_Grid'][(data['Alt_Grid'] >= data['Range_O3'][0]) & (data['Alt_Grid'] <= data['Range_O3'][1])]

    #average the ozone profiles
    o3 = np.zeros((len(o3_alts), len(mjds)))
    for idx,mjd in enumerate(mjds):
        good = (data['mjd'] > mjd) & (data['mjd'] < mjd+ time_res)
        with warnings.catch_warnings(): #there will be all nans at high/low altitudes, its fine
            warnings.simplefilter("ignore", category=RuntimeWarning)
            o3[:,idx] = np.nanmean(data['O3'][good,:], axis=0)

    #make the plot
    plt.contourf(Time(mjds+time_res/2, format='mjd').datetime, o3_alts, o3, levels=np.arange(0,7e12,1e11),extend='both')
    plt.colorbar()
    plt.clim(0,7e12)
    plt.ylabel('Altitude [km]')
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=45)
    plt.ylim(15,50)
    plt.show()

if __name__ == "__main__":
    ozone_time_series('C:\\path\\to\\data')