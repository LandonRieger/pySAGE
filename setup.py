from os import path
from setuptools import setup, find_packages
import versioneer

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='pysagereader',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='SAGE II v7.0 binary file reader',
      long_description=long_description,
      long_description_content_type='text/x-rst',
      author='USASK ARG',
      author_email='landon.rieger@usask.ca',
      license='MIT',
      url='https://github.com/LandonRieger/pySAGE.git',
      packages=find_packages(),
      install_requires=['numpy', 'pandas', 'xarray', 'click'],
      python_requires='>=3.6',
      )