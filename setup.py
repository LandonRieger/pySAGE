from setuptools import setup, find_packages

setup(name='pysagereader',
      version='0.2.0',
      description='SAGE binary file readers',
      author='USASK ARG',
      author_email='landon.rieger@usask.ca',
      license='MIT',
      url='https://github.com/LandonRieger/pySAGE.git',
      packages=find_packages(),
      install_requires=['astropy', 'xarray']
      )