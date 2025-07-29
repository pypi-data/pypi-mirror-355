# Release v2.0.0
* Dropped support for Python3.8 and earlier.
* Migrated iblox to use `uv` for project managment [0327f77]
* Updated Bitbucket Pipelines to use `uv` [eb8388c]
* Added Makefile for common operations (and docker-based testing) [8f7bcab]
* Added more unit tests for `iblox.ipv4addr_obj` [6b3dcab]

# Release v1.5.8
* Added Python3.9 to testing [64111eb]
* Migrating PyPI deployment to use twine [2f92be4]

# Release v1.5.7
* Added testing support for Python3.8 [1a0a149]

# Release v1.5.6
* Added more unit tests
* Unit tests now use requests_mock module. [f46aac5]
* Fixing bug where Infoblox.verify conflicting with Infoblox.verify() [ff4d3ad]
* Adding caches and documentation builds to bitbucket-pipelines. [3d07196]
* Adding Python3.7 to the testing suite [bd09be1]

# Release v1.5.5
* Dropping testing for Python2.6 and Python3.5.  Gotta keep people moving up in the world. [08b0d44]

# Release v1.5.4
* Updated documentation hosting [57310db]

# Release v1.5.3
* Code cleanup [d95b707]
* Actually building some documentation for the module... imagine that! [4dd9272]
* Automating testing with Tox [72e6373]
* Moving to built-in exception classes. [c5dd634]
* Going to host iblox documentation at pythonhosted.org [1125d53]

# Release v1.5.2
* Protecting internal calls so that Infoblox could be sublcassed if needed [150b89e]

# Release v1.5.1
* Use params= instead of data= for get requests - [Merge Request #1]

# Release v1.5
* Now compatible with Python 2.7.x and Python 3.5.x
* Infoblox class can now be used with Python's 'with' statement

# Release v1.4.6
* Fixed bugs in `add_alias` and `delete_alias shortcuts
* Renamed project to iblox (Infoblox as a module name was taken)
* Releasing as Open Source

# Release v1.4.4
* Fixed Bug if *disable_warnings* property is not available in requests module

# Release v1.4.3
* Fixed Bugs with Call Function (Using POST data rather than URL arguments)
* Disabling SSL warnings (from request module) if ssl verification is turned off

# Release v1.4.2
* Fixed Bug in `_verify_` method when `_ref` argument doesn't exist
* Fixed Bug with `_return_type` property when adding/deleting records

# Release v1.4
* Added `delete_alias` shortcut for deleting aliases/CNAMES from a host
* Added `add_host_ip` shortcut for adding IPv4 Addresses to a host
* Added `view` property for specifying default view to use when creating objects
* Added kwarg modifiers for
  * `_regex`
  * `_greaterthan`
  * `_lessthan`
* Added `call` method for accessing object functions via that WAPI (e.g. get_next_available_ip)
* New Exception Classes

# Release 1.2
* Added `__fix_plus__` method to convert kwargs that end in `_plus` to end in `+`
* Added `add_alias` shortcut for adding aliases/CNAMES to a host

# Release v1.1
* Module now caches session info when talking to the Infoblox WAPI
* Rewritten `add`, `delete`, and `modify` commands
* Changed kwarg `record` to `objtype`
* Ensuring all data passed to Infoblox WAPI is converted to JSON
* Renamed `find_host` with `get_host` for all methods

# Release v1.0
* Created Infoblox class
* Created `add`, `get`, `delete`, `modify` methods for Infoblox Python Module
