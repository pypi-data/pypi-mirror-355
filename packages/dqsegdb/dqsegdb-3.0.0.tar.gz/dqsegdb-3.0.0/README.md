dqsegdb
=======

[![PyPI version](https://badge.fury.io/py/dqsegdb.svg)](http://badge.fury.io/py/dqsegdb)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/dqsegdb.svg)](https://anaconda.org/conda-forge/dqsegdb/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/dqsegdb.svg)

[![License](https://img.shields.io/pypi/l/dqsegdb.svg)](https://choosealicense.com/licenses/gpl-3.0/)
[![DOI](https://img.shields.io/badge/DOI-10.1016/j.softx.2021.100677-blue)](https://img.shields.io/badge/DOI-10.1016/j.softx.2021.100677-blue)

[![Build status](https://git.ligo.org/computing/dqsegdb/client/badges/master/pipeline.svg)](https://git.ligo.org/computing/dqsegdb/client/-/pipelines)
![Code coverage](https://git.ligo.org/computing/dqsegdb/client/badges/main/coverage.svg)

DQSEGDB client library and functions

Please see documentation at: 

https://git.ligo.org/computing/dqsegdb/client/

The DQSEGDB client package should be installed and available for use in the standard IGWN Conda environments (e.g., `igwn-py39`; see https://computing.docs.ligo.org/conda/ for details).

The package can also be installed from PyPI: `pip install dqsegdb` or `python3 -m pip install dqsegdb`.

The package can also be installed from source:

```
# Clone the repository:
git clone https://git.ligo.org/computing/dqsegdb/client.git

# cd into the repo
cd client

# "Build" the package, placing binaries and libraries into standard directories
python3 -m pip install .
```

DQSegDB architecture as used by IGWN
=======
![diagram of DQSegDB system architecture](system_architecture_20200212.png)
