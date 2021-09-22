import pytest
from pysagereader.sage_ii_reader import SAGEIILoaderV700
import os


def test_loader():

    sage = SAGEIILoaderV700(os.path.join(os.path.dirname(__file__), 'data'))
    data = sage.load_data(min_date='1984', max_date='1985')
    assert len(data.time) == 238
