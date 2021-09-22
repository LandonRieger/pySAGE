import os
import click
import pandas as pd
from pysagereader import SAGEIILoaderV700


@click.command()
@click.option('-i', '--input_folder', default=None, help='location of sage ii binary files')
@click.option('-o', '--output_folder', default=None, help='output location of netcdf files')
@click.option('-t', '--time_res', default='none', help='time resolution of output files, none, year, month or day accepted or'
                                                       'a frequency recognized by pandas, eg. 7D')
@click.option('-s', '--start_time', default='1985', help='earliest record to include')
@click.option('-e', '--end_time', default='2006', help='last record to include')
def make_netcdf(input_folder, output_folder, time_res, start_time, end_time):
    """
    Create netcdf files from the SAGE II binary files
    """
    if input_folder is None:
        input_folder = os.getcwd()
    if output_folder is None:
        output_folder = os.getcwd()

    if time_res == 'none':
        dates = [pd.Timestamp(start_time), pd.Timestamp(end_time)]
    elif time_res in ['year', 'yearly', 'AS']:
        dates = pd.date_range(start_time, end_time, freq='AS')
    elif time_res in ['month', 'monthly', 'MS']:
        dates = pd.date_range(start_time, end_time, freq='MS')
    elif time_res in ['day', 'daily', 'D']:
        dates = pd.date_range(start_time, end_time, freq='D')
    else:
        try:
            dates = pd.date_range(start_time, end_time, freq=time_res)
        except ValueError:
            raise ValueError('invalid time resolution, try none, year, month, or day')

    for start, end in zip(dates[0:-1], dates[1:]):
        s = SAGEIILoaderV700(input_folder,
                             species=['aerosol', 'h2o', 'no2', 'ozone', 'background'],
                             output_format='xarray',
                             return_separate_flags=True,
                             normalize_percent_error=True)

        data, flag = s.load_data(min_date=start.isoformat(), max_date=end.isoformat())

        filename = os.path.join(output_folder, 'SAGE_II_' +
                                time_format(start, end, time_res) +
                                '_' +
                                str(s.version) + '.nc')
        data.to_netcdf(filename)
        flag.to_netcdf(filename, group='flags', mode='a')


def time_format(a, b, time_res):

    if time_res in ['year', 'yearly', 'AS']:
        return '{0}'.format(a.date().year)
    elif time_res in ['month', 'monthly', 'MS']:
        return '{0}{1:02d}'.format(a.date().year, a.date().month)
    elif time_res in ['day', 'daily', 'D']:
        return '{0}{1:02d}{2:02d}'.format(a.date().year, a.date().month, a.date().day)
    else:
        return '{0}{1:02d}{2:02d}_{3}{4:02d}{5:02d}'.format(a.date().year, a.date().month, a.date().day,
                                                            b.date().year, b.date().month, b.date().day)


if __name__ == '__main__':
    make_netcdf()
