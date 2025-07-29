#
# Copyright (c) 2015-2019 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""
Generic test cases for pyams_workflow doctests
"""

__docformat__ = 'restructuredtext'

import os
import sys

from persistent import Persistent
from zope.component import getUtility
from zope.container.contained import Contained
from zope.interface import Interface, implementer

from pyams_utils.adapter import adapter_config
from pyams_utils.traversing import get_parent
from pyams_workflow.interfaces import IWorkflow, IWorkflowManagedContent, \
    IWorkflowPublicationSupport


def get_package_dir(value):
    """Get package directory"""

    package_dir = os.path.split(value)[0]
    if package_dir not in sys.path:
        sys.path.append(package_dir)
    return package_dir


class IWfContent(Interface):
    """Test content version marker interface"""


class IContent(Interface):
    """Test content marker interface"""


@implementer(IWfContent, IWorkflowPublicationSupport)
class WfContent(Persistent, Contained):
    """Content version class"""


@adapter_config(required=IWfContent, provides=IWorkflow)
def wf_content_workflow_adapter(context):
    """Content workflow adapter"""
    content = get_parent(context, IContent)
    return getUtility(IWorkflow, name=content.workflow_name)


@implementer(IContent, IWorkflowManagedContent)
class Content:
    """Content class"""
