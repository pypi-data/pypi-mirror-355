# -*- coding: utf-8 -*-

import glob
import os.path
import versioneer
from setuptools import (setup, find_packages)

PACKAGENAME = 'dqsegdb'
DESCRIPTION = 'Client library for DQSegDB'
LONG_DESCRIPTION = 'This package installs client tools and libraries for accessing the LIGO/IGWN Data Quality Segment Database (DQSegDB = DQSEGDB).'   # noqa: 501
AUTHOR = 'Ryan Fisher'
AUTHOR_EMAIL = 'ryan.fisher@ligo.org'
LICENSE = 'GPLv3'

# -- versioning ---------------------------------------------------------------

__version__ = versioneer.get_version()
cmdclass = versioneer.get_cmdclass()

# -- setup ---------------------------------------------------------------------

# Use the find_packages tool to locate all packages and modules
packagenames = find_packages()

# glob for all scripts
if os.path.isdir('bin'):
    scripts = glob.glob(os.path.join('bin', '*'))
else:
    scripts = []

setup(name=PACKAGENAME,
      cmdclass=cmdclass,
      version=__version__,
      description=DESCRIPTION,
      url="https://git.ligo.org/computing/dqsegdb/client",
      packages=packagenames,
      ext_modules=[],
      scripts=scripts,
      setup_requires=['setuptools'],
      install_requires=[
          'gpstime',
          'igwn-auth-utils',
          'igwn-ligolw>=2.0.0',
          'lalsuite',
          'igwn-segments',
          'lscsoft-glue>=3.0.1',
          'pyOpenSSL>=0.14',
          'pyRXP',
      ],
      provides=[PACKAGENAME],
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      long_description=LONG_DESCRIPTION,
      zip_safe=False,
      )
