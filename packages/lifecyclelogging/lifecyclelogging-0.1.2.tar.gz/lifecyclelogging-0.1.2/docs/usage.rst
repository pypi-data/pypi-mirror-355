===========
Usage Guide
===========

==============
Configuration
==============

=====================
Logger Initialization
=====================

.. code-block:: python

   from lifecyclelogging import Logging

   logger = Logging(
       enable_console=True,     # Enable console output
       enable_file=True,        # Enable file output
       logger_name="myapp",     # Custom logger name
       log_file_name="app.log", # Custom log file name
       default_storage_marker="app",  # Default marker for storing messages
       enable_verbose_output=True,    # Enable verbose logging
       verbosity_threshold=2,         # Set verbosity level (1-5)
       allowed_levels=["info", "warning"],  # Only store these levels
       denied_levels=["debug"]             # Don't store these levels
   )

===========
Log Levels
===========

Available log levels:

.. code-block:: python

   logger.logged_statement("Debug info", log_level="debug")
   logger.logged_statement("General info", log_level="info")
   logger.logged_statement("Warning message", log_level="warning")
   logger.logged_statement("Error occurred", log_level="error")
   logger.logged_statement("Critical failure", log_level="critical")

===============
Message Storage
===============

===============
Context Markers
===============

Prefix messages with context:

.. code-block:: python

   logger.logged_statement(
       "Starting process",
       context_marker="STARTUP",
       log_level="info"
   )

   # Output: [STARTUP] Starting process

===============
Storage Markers
===============

Store messages for later retrieval:

.. code-block:: python

   logger.logged_statement(
       "Database connected",
       storage_marker="DB",
       log_level="info"
   )

   # Access stored messages
   db_messages = logger.stored_messages["DB"]

==========
JSON Data
==========

==============
Unlabeled JSON
==============

.. code-block:: python

   logger.logged_statement(
       "API request",
       json_data={
           "method": "POST",
           "endpoint": "/users",
           "status": 200
       },
       log_level="info"
   )

============
Labeled JSON
============

.. code-block:: python

   logger.logged_statement(
       "Request/Response",
       labeled_json_data={
           "request": {"method": "GET", "url": "/api/v1/users"},
           "response": {"status": 200, "count": 5}
       },
       log_level="info"
   )

=================
Verbosity Control
=================

=============
Basic Control
=============

.. code-block:: python

   # Will be logged only if enable_verbose_output=True
   logger.logged_statement(
       "Detailed info",
       verbose=True,
       log_level="debug"
   )

================
Verbosity Levels
================

.. code-block:: python

   # Configure verbosity
   logger = Logging(
       enable_verbose_output=True,
       verbosity_threshold=2  # Accept messages with verbosity <= 2
   )

   # Will be logged (verbosity <= threshold)
   logger.logged_statement(
       "Medium detail",
       verbose=True,
       verbosity=2,
       log_level="debug"
   )

   # Won't be logged (verbosity > threshold)
   logger.logged_statement(
       "High detail",
       verbose=True,
       verbosity=3,
       log_level="debug"
   )

================
Verbosity Bypass
================

.. code-block:: python

   # Add marker to bypass list
   logger.verbosity_bypass_markers.append("IMPORTANT")

   # Will be logged regardless of verbosity settings
   logger.logged_statement(
       "Critical info",
       context_marker="IMPORTANT",
       verbose=True,
       verbosity=5,
       log_level="debug"
   )

=====================
Environment Variables
=====================

The following environment variables are supported:

- ``LOG_LEVEL``: Set the default log level
- ``LOG_FILE_NAME``: Set the log file name
- ``OVERRIDE_TO_CONSOLE``: Force console output (True/False)
- ``OVERRIDE_TO_FILE``: Force file output (True/False)

==============
Best Practices
==============

1. **Log Level Selection**
   - Use "debug" for detailed troubleshooting
   - Use "info" for general operational events
   - Use "warning" for potentially harmful situations
   - Use "error" for error events that might still allow the application to continue
   - Use "critical" for critical errors that prevent program execution

2. **Structured Data**
   - Use json_data for single objects
   - Use labeled_json_data for multiple related objects
   - Keep data structures clean and readable

3. **Markers**
   - Use consistent naming conventions
   - Group related functionality
   - Consider hierarchical markers (e.g., "database.query", "database.connection")

4. **Performance**
   - Use appropriate verbosity levels
   - Consider log rotation for file outputs
   - Monitor log file sizes
