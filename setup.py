from setuptools import setup, find_packages
import versioneer

setup(name='pysagereader',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='SAGE binary file readers',
      author='USASK ARG',
      author_email='landon.rieger@usask.ca',
      license='MIT',
      url='https://github.com/LandonRieger/pySAGE.git',
      packages=find_packages(),
      install_requires=['xarray']
      )