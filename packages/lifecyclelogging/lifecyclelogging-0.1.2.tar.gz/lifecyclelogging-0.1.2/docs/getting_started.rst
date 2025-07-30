===============
Getting Started
===============

============
Installation
============

.. code-block:: bash

   pip install lifecyclelogging

===========
Quick Start
===========

===========
Basic Usage
===========

.. code-block:: python

   from lifecyclelogging import Logging

   # Initialize logger
   logger = Logging(
       enable_console=True,  # Enable console output
       enable_file=True,     # Enable file output
       logger_name="my_app"
   )

   # Basic logging
   logger.logged_statement("Basic message", log_level="info")

   # With context marker
   logger.logged_statement(
       "Message with context",
       context_marker="STARTUP",
       log_level="info"
   )

   # With JSON data
   logger.logged_statement(
       "Message with data",
       json_data={"key": "value"},
       log_level="debug"
   )

===============
Storage Markers
===============

Store and retrieve related messages:

.. code-block:: python

   # Store messages under a marker
   logger.logged_statement(
       "Important event",
       storage_marker="EVENTS",
       log_level="info"
   )

   # Access stored messages
   events = logger.stored_messages["EVENTS"]

=================
Verbosity Control
=================

Control output detail level:

.. code-block:: python

   logger = Logging(
       enable_verbose_output=True,
       verbosity_threshold=2
   )

   # Only logged if verbosity threshold allows
   logger.logged_statement(
       "Detailed debug info",
       verbose=True,
       verbosity=2,
       log_level="debug"
   )

=================
Development Setup
=================

.. code-block:: bash

   # Install development dependencies
   pip install -e ".[dev,test,docs]"

   # Run tests
   make test

   # Run linting and type checks
   make check

   # Build documentation
   make docs
