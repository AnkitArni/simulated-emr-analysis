# emr-analysis

A simple analysis and visualisation package for simulated Electronic Medical Records (EMR) data. This project is for an assignment and is currently available on [TestPyPI](https://test.pypi.org/project/emr-analysis/)

[![Read the Docs](https://readthedocs.org/projects/pip/badge/?version=latest)](https://emr-analysis.readthedocs.io/en/latest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380+/)

<hr>

## Why emr-analysis?
The adoption of Electronic Medical Records (EMR) in healthcare has vastly increased in recent years, particularly in view of the requirements of Meaningful Use of patient data. However, they are grossly under-utilised for the following reasons:
1. Not all the data stored in EMRs is useful, and as such, makes it difficult to build a generalised solution for data analysis.
2. Patient confidentiality compliance laws severely limit the usage of EMRs in conjunction with other sources of medical data.

Uri Kartoun [[1]](#1) attempted to tackle the second issue by creating simulated EMR data that closely resembles the actual data. Therefore, we use the dataset generated on [EMRBots](http://www.emrbots.org/) to create an analysis and visualisation package that could possibly be used in a real-world setting.

<hr>

## Features:
1. Loads data in either text or zip file formats, that match the standard EMR format types.
2. Plot relevant summary statistics of the EMR data.
3. Create interactive dashboards that show individual summaries and also provide a quicksearch feature.

<hr>

## Notes:
1. Currently processes 4 kinds of files, identified by both filename and data header patterns:
    * AdmissionsCorePopulatedTable.txt
    * AdmissionsDiagnosesCorePopulatedTable.txt
    * LabsCorePopulatedTable.txt
    * PatientCorePopulatedTable.txt
2. The dependency module `python-magic-bin` is basically a Python wrapper around libmagic, please refer to their [PyPI page](https://pypi.org/project/python-magic-bin/) if any issues are encountered.

<hr>

## References:
<a id="1">[1]</a> Kartoun, U. (2019). Advancing informatics with electronic medical records bots (EMRBots). Software Impacts, 2, 100006. https://doi.org/10.1016/j.simpa.2019.100006
