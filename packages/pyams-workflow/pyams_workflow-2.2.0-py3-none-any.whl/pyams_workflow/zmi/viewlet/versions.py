#
# Copyright (c) 2015-2021 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS_workflow.zmi.viewlet.versions module

This module defines a viewlet which can be used to display a dropdown menu
of existing content versions.
"""

from pyramid.decorator import reify
from zope.interface import Interface

from pyams_skin.viewlet.menu import DropdownMenu, MenuItem
from pyams_utils.registry import get_utility
from pyams_utils.traversing import get_parent
from pyams_utils.url import absolute_url
from pyams_viewlet.viewlet import viewlet_config
from pyams_workflow.interfaces import IWorkflow, IWorkflowManagedContent, IWorkflowState, \
    IWorkflowVersion, IWorkflowVersions
from pyams_zmi.interfaces import IAdminLayer
from pyams_zmi.interfaces.viewlet import IToolbarViewletManager


__docformat__ = 'restructuredtext'

from pyams_workflow import _  # pylint: disable=ungrouped-imports


@viewlet_config(name='pyams_workflow.versions',
                context=IWorkflowVersion, layer=IAdminLayer, view=Interface,
                manager=IToolbarViewletManager, weight=100)
class WorkflowVersionsMenu(DropdownMenu):
    """Workflow versions menu viewlet"""

    status = 'info'
    css_class = 'btn-sm'

    @reify
    def workflow(self):
        """Workflow property getter"""
        content = get_parent(self.context, IWorkflowManagedContent)
        return get_utility(IWorkflow, name=content.workflow_name)

    @property
    def label(self):
        """Label getter"""
        translate = self.request.localizer.translate
        state = IWorkflowState(self.context)
        return translate(_("Version {id} - {state}")).format(
            id=state.version_id,
            state=translate(self.workflow.get_state_label(state.state)))

    def _get_viewlets(self):
        translate = self.request.localizer.translate
        for version in IWorkflowVersions(self.context).get_last_versions(count=0):
            state = IWorkflowState(version)
            item = MenuItem(version, self.request, self.view, self)
            item.label = translate(_("Version {id} - {state}")).format(
                id=state.version_id,
                state=translate(self.workflow.get_state_label(state.state)))
            item.icon_class = 'fas fa-arrow-right'
            if version is self.context:
                item.css_class = 'bg-primary text-white'
            else:
                item.icon_class = f'{item.icon_class} text-secondary'
            item.href = absolute_url(version, self.request,
                                     'admin#{}'.format(self.request.view_name))
            yield 'version_{}'.format(state.version_id), item
