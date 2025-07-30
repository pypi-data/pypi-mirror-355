IDA Domain API Documentation
============================

The IDA Domain API provides a **Domain Model** on top of the IDA SDK, allowing interaction with IDA SDK components via Python.

🚀 Features
-----------

- Exposes a Domain Model on top of IDA SDK functions to Python
- Pure Python implementation
- Easy installation via pip
- Comprehensive API for reverse engineering tasks

⚙️ Quick Start
--------------

Installation
~~~~~~~~~~~~

Set the ``IDADIR`` environment variable to point to your IDA installation directory:

.. code-block:: bash

   export IDADIR="/Applications/IDA Professional 9.1.app/Contents/MacOS/"

.. note::
   If you have already installed and configured the ``idapro`` Python package, setting ``IDADIR`` is not required.

Install from PyPI (recommended):

.. code-block:: bash

   pip install ida-domain

Visit the `PyPI package page <https://pypi.org/project/ida-domain/>`_ for more details and version history.

Or install from source:

.. code-block:: bash

   git clone git@github.com:HexRaysSA/ida-api-domain.git
   cd ida-api-domain
   pip install .

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from ida_domain import Database

   # Open a database
   db = Database()
   if db.open("/path/to/your/binary"):
       # Get all functions
       for func in db.functions.get_all():
           print(f"Function: {db.functions.get_name(func)}")

       # Close the database
       db.close(save=False)

📚 API Reference
----------------

.. toctree::
   :maxdepth: 2
   :caption: API Documentation:

   api

📖 Guides and Examples
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Guides:

   examples
   installation

🔗 Additional Resources
-----------------------

* **PyPI Package**: `ida-domain on PyPI <https://pypi.org/project/ida-domain/>`_
* **Source Code**: `GitHub Repository <https://github.com/HexRaysSA/ida-api-domain>`_
* **Issues**: `Bug Reports <https://github.com/HexRaysSA/ida-api-domain/issues>`_
* **License**: MIT License

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
