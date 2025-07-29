Changelog
=========

2.2.0
-----
 - added method to content workflow publication info interface to apply first publication date
   on content "real" publication

2.1.5
-----
 - updated workflow content displayed date vocabulary to handle un-versioned contents

2.1.4
-----
 - updated doctest for last PyAMS_zmi compatibility
 - added support for Python 3.12

2.1.3
-----
 - updated "get_version()" method to exclude deleted versions from result
   when no version index is specified

2.1.2
-----
 - switched default timezone to UTC

2.1.1
-----
 - updated doctests

2.1.0
-----
 - added support for dividers in workflow transitions dropdown menu
 - added marker interface to history table to support extension viewlets
 - updated principal getter when firing transition

2.0.3
-----
 - added check in versions helper for contents not supporting versioning

2.0.2
-----
 - updated ZMI dependency
 - updated doctests based on last ZMI release

2.0.1
-----
 - updated modal forms title

2.0.0
-----
 - upgraded to Pyramid 2.0

1.3.3
-----
 - updated default view permission
 - automatically get last version if specified version ID is -1

1.3.2
-----
 - updated base transition form renderer

1.3.1
-----
 - added helper class to handle publication info of "hidden" contents
 - added support for Python 3.11

1.3.0
-----
 - added helper functions to get last versions of a given content
 - added support for Python 3.10
 - updated translations
 - updated versions menu status

1.2.0
-----
 - added workflow label
 - added workflow information property to keep first publication date of a managed content,
   including all it's versions
 - don't allow setting of publication date before current datetime
 - remove workflow management task interface from package
 - small updates in base workflow transition management form
 - updated style of workflow versions menu options
 - use iterator in versions sub-locations adapter

1.1.1
-----
 - import Invalid from zope.interface instead of zope.interface.interfaces

1.1.0
-----
 - removed support for Python < 3.7
 - updated workflow content transition form
 - added check against previous state before applying any transition
 - added workflow adapter for any IWorkflowVersion content
 - added timezone to all generated datetimes

1.0.1
-----
 - updated Gitlab-CI configuration
 - removed Travis-CI configuration

1.0.0
-----
 - initial release
