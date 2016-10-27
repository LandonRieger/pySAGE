from setuptools import setup, find_packages

setup(name='pysagereader',
      version='0.1.0',
      description='SAGE binary file readers',
      author='USASK ARG',
      license='MIT',
      url='https://github.com/LandonRieger/pySAGE.git',
      packages=find_packages(),
      install_requires=['numpy', 'astropy']
      )