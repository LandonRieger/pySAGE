from setuptools import setup, find_packages

setup(name='pysagereader',
      version='0.1.0',
      description='SAGE binary file readers',
      author='USASK ARG',
      url='https://github.com/LandonRieger/pySAGE.git',
      packages=find_packages(),
      requires=['numpy', 'astropy'],
      )