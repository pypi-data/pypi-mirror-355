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

"""PyAMS_workflow.zmi.viewlet.transitions module

This module defines a viewlet which can be used to display a dropdown menu
of all available content transitions.
"""

from zope.interface import Interface

from pyams_skin.viewlet.menu import DropdownMenu, MenuDivider, MenuItem
from pyams_utils.registry import get_utility
from pyams_utils.traversing import get_parent
from pyams_utils.url import absolute_url
from pyams_viewlet.viewlet import viewlet_config
from pyams_workflow.interfaces import IWorkflow, IWorkflowInfo, IWorkflowManagedContent, \
    IWorkflowVersion
from pyams_zmi.interfaces import IAdminLayer
from pyams_zmi.interfaces.viewlet import IToolbarViewletManager


__docformat__ = 'restructuredtext'

from pyams_workflow import _  # pylint: disable=ungrouped-imports


class TransitionMenuItem(MenuItem):
    """Workflow transition menu item"""

    def __init__(self, context, request, view, manager, transition):
        # pylint: disable=too-many-arguments
        super().__init__(context, request, view, manager)
        self.label = transition.title
        self.icon_class = transition.user_data.get('menu_icon_class') or 'fa'
        self.href = '{url}?workflow.widgets.transition_id={transition}'.format(
            url=absolute_url(context, request,
                             transition.user_data.get('view_name', 'wf-transition.html')),
            transition=transition.transition_id)
        self.modal_target = True
        self.weight = transition.order * 10


@viewlet_config(name='pyams_workflow.transitions',
                context=IWorkflowVersion, layer=IAdminLayer, view=Interface,
                manager=IToolbarViewletManager, weight=200)
class WorkflowTransitionsMenu(DropdownMenu):
    """Workflow transitions menu"""

    status = 'danger'
    css_class = 'btn-sm'
    label = _("Change status...")

    def _get_viewlets(self):
        viewlets = []
        content = get_parent(self.context, IWorkflowManagedContent)
        wf = get_utility(IWorkflow, name=content.workflow_name)  # pylint: disable=invalid-name
        if wf is None:
            return viewlets
        info = IWorkflowInfo(self.context)
        for transition_id in info.get_manual_transition_ids():
            transition = wf.get_transition_by_id(transition_id)
            if transition.user_data.get('menu_divider'):
                divider = MenuDivider(self.context, self.request, self.view, None)
                divider.weight = (transition.order * 10) - 1
                viewlets.append((f'{transition_id}_divider', divider))
            menu = TransitionMenuItem(self.context, self.request, self.view, self, transition)
            viewlets.append((transition_id, menu))
        return sorted(viewlets, key=lambda x: x[1].weight)
