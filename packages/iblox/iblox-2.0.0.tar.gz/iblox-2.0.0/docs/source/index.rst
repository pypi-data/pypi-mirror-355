.. iblox documentation master file

.. _home:

Iblox Python Module
===================

If you are working with the Infoblox WAPI then you need iblox.  It is a highly extensible Python wrapper for the WAPI and can
be used across many versions of Infoblox.  That is what makes iblox stand out from other modules for Infoblox,
it was designed not to contain a bunch of aliases for doing things via the WAPI but actually allow you to control every
aspect of the WAPI via Python.


Getting Started
---------------

Installing Iblox
~~~~~~~~~~~~~~~~

Getting started with iblox is easy since the module is pip installable:

.. code-block:: bash

    pip install iblox

Infoblox Objects
~~~~~~~~~~~~~~~~

Everything you do with the Infoblox WAPI starts with the :code:`Infoblox` class, which creates a session based connection
to the WAPI.  Because it uses sessions it means that your authentication "call" will only be made once to the WAPI.

.. code-block:: python

    from iblox import Infoblox

    iblox_conn = iblox.Infoblox('https://infoblox.example.com/wapi/v1.7.1/', username='admin', password='infoblox')
    print(iblox_conn.get(objtype='record:host', name='infoblox.example.com'))

Notice here that I didn't close the connection.  That is because the WAPI is a REST API and doesn't require sessions to be
closed.  All the session info that you need for the duration of your script is stored in the :code:`Infoblox` object when it is
created.

API Documentation
-----------------

To learn what calls are available when accessing the WAPI via an Infoblox instance, please read up on the iblox API:

.. toctree::
   :maxdepth: 1

   iblox

If you are looking for what calls you can make to the Infoblox WAPI then be sure to download the **WAPI Documentation** via
the link in the right "drawer" of the Infoblox Grid Manager web interface.

Examples
--------
If you are looking for examples of how the iblox module can be used be sure to check out the `EXAMPLES file on Bitbucket`_

Compatibility
-------------

This project currently is tested with all [supported versions of Python](https://devguide.python.org/versions/)

Links
-----

* :ref:`genindex`

.. _EXAMPLES file on Bitbucket: https://bitbucket.org/isaiah1112/infoblox
