DRF SPECTACULAR EXTRAS
======================

.. image:: https://img.shields.io/pypi/v/drf-spectacular-extras
   :target: https://pypi.org/project/drf-spectacular-extras/
   :alt: PyPI

.. image:: https://codecov.io/gh/huynguyengl99/drf-spectacular-extras/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/huynguyengl99/drf-spectacular-extras
   :alt: Code Coverage

.. image:: https://github.com/huynguyengl99/drf-spectacular-extras/actions/workflows/test.yml/badge.svg?branch=main
   :target: https://github.com/huynguyengl99/drf-spectacular-extras/actions/workflows/test.yml
   :alt: Test

Additional extensions and utilities for `drf-spectacular <https://drf-spectacular.readthedocs.io/>`_.

Features
--------

🚀 **Additional API Documentation UIs**

* **Scalar UI Integration** - Modern, interactive API documentation with Scalar
* Easy integration with existing drf-spectacular setups
* Customizable UI settings and themes

🔧 **Enhanced Utilities**

* Extended configuration options for API documentation
* Additional view classes and mixins
* Better developer experience tools

Installation
------------

.. code-block:: bash

    pip install drf-spectacular-extras

Quick Start
-----------

1. Add ``drf_spectacular_extras`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        'drf_spectacular',
        'drf_spectacular_extras',
        # ...
    ]

2. Configure the Scalar UI (optional):

.. code-block:: python

    SPECTACULAR_EXTRAS_SETTINGS = {
        'SCALAR_UI_SETTINGS': {
            'theme': 'purple',
            'layout': 'modern',
            # Add any Scalar configuration options
        },
    }

3. Add Scalar UI to your URLs:

.. code-block:: python

    from drf_spectacular_extras.views import SpectacularScalarView

    urlpatterns = [
        # Your existing spectacular URLs
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

        # Add Scalar UI
        path('api/schema/scalar/',
             SpectacularScalarView.as_view(url_name='schema'),
             name='scalar'),
    ]

4. Visit ``/api/schema/scalar/`` to see your API documentation with Scalar UI! 🎉

Configuration
-------------

Scalar UI Settings
~~~~~~~~~~~~~~~~~~

You can customize the Scalar UI by configuring ``SPECTACULAR_EXTRAS_SETTINGS``:

.. code-block:: python

    SPECTACULAR_EXTRAS_SETTINGS = {
        'SCALAR_UI_SETTINGS': {
            'theme': 'purple',           # Theme: 'default', 'purple', 'blue', etc.
            'layout': 'modern',          # Layout style
            'showSidebar': True,         # Show/hide sidebar
            'hideDownloadButton': False, # Hide download button
            'searchHotKey': 'k',         # Search hotkey
            # See Scalar docs for all available options
        },
        'SCALAR_DIST': 'https://cdn.jsdelivr.net/npm/@scalar/api-reference@latest',
    }

Requirements
------------

* Python 3.10+
* Django 4.2+
* djangorestframework 3.14+
* drf-spectacular 0.28.0+

Why DRF Spectacular Extras?
---------------------------

While `drf-spectacular <https://drf-spectacular.readthedocs.io/>`_ provides excellent OpenAPI 3 schema generation and comes with Swagger UI and ReDoc, this package extends it with:

* **Modern UI Options**: Access to cutting-edge documentation UIs like Scalar
* **Enhanced Developer Experience**: Additional utilities and configuration options
* **Easy Integration**: Drop-in compatibility with existing drf-spectacular setups
* **Active Maintenance**: Regular updates to support the latest UI frameworks

Contributing
------------

We welcome contributions! Please see our `Contributing Guide <https://drf-spectacular-extras.readthedocs.io/en/latest/contributing.html>`_ for details.

Development setup:

.. code-block:: bash

    git clone https://github.com/huynguyengl99/drf-spectacular-extras.git
    cd drf-spectacular-extras
    uv sync --all-extras
    docker compose up  # Start test database
    python sandbox/manage.py migrate
    python sandbox/manage.py runserver

Documentation
-------------

Please visit `DRF Spectacular Extras docs <https://drf-spectacular-extras.readthedocs.io/>`_ for complete documentation.

License
-------

This project is licensed under the MIT License - see the `LICENSE <LICENSE>`_ file for details.

Acknowledgments
---------------

* Built on top of the excellent `drf-spectacular <https://drf-spectacular.readthedocs.io/>`_ package
* Scalar UI integration powered by `Scalar <https://github.com/scalar/scalar>`_
