*************
UDS - ADDRESS
*************

|LatestVersion| |PythonVersions| |PyPIStatus| |TotalDownloads| |MonthlyDownloads| |Licence|

This is extension to `py-uds`_ package with addresses of ECUs.


ECU address
-----------
If you look for an address of a certain ECU, either search by spare part number and bus type in
`ecu section <https://github.com/mdabrowski1990/uds-address/tree/main/uds_address/ecu>`_
or by OEM, carline and production year and bus, e.g.
`Hyundai i20 2021, CAN bus accessible via OBD-2
<https://github.com/mdabrowski1990/uds-address/blob/main/uds_address/hyundai/i20/year_2021/can_obd2.py>`_.


How to add ECU?
---------------
If you know an address of some ECU (or a group of ECUs), please create
`an issue <https://github.com/mdabrowski1990/uds-address/issues/new?template=01_add_ecu.md>`_
and provide all the required details, so we could use this information as part of this package.


Documentation
-------------
This package contains only addresses of ECUs. For full user documentation about UDS go to: https://uds.readthedocs.io/


Contact
-------
- e-mail: uds-package-development@googlegroups.com
- group: `UDS package development`_
- discord: https://discord.gg/y3waVmR5PZ

If you want to become a contributor, please read `CONTRIBUTING.md`_ file.


.. _CONTRIBUTING.md: https://github.com/mdabrowski1990/uds-address/blob/main/CONTRIBUTING.md

.. _UDS package development: https://groups.google.com/g/uds-package-development/about

.. _py-uds: https://github.com/mdabrowski1990/uds


.. |LatestVersion| image:: https://img.shields.io/pypi/v/py-uds-address.svg
   :target: https://pypi.python.org/pypi/py-uds-address
   :alt: The latest Version of UDS package

.. |PythonVersions| image:: https://img.shields.io/pypi/pyversions/py-uds-address.svg
   :target: https://pypi.python.org/pypi/py-uds-address/
   :alt: Supported Python versions

.. |PyPIStatus| image:: https://img.shields.io/pypi/status/py-uds-address.svg
   :target: https://pypi.python.org/pypi/py-uds-address/
   :alt: PyPI status

.. |TotalDownloads| image:: https://pepy.tech/badge/py-uds-address
   :target: https://pepy.tech/project/py-uds-address
   :alt: Total PyPI downloads

.. |MonthlyDownloads| image:: https://pepy.tech/badge/py-uds-address/month
   :target: https://pepy.tech/project/py-uds-address
   :alt: Monthly PyPI downloads

.. |Licence| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://lbesson.mit-license.org/
   :alt: License Type
