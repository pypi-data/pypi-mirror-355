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

"""PyAMS_workflow.zmi.transition module

This module defines a base transition form.
"""

from pyramid.decorator import reify
from zope.lifecycleevent import ObjectModifiedEvent

from pyams_form.ajax import ajax_form_config
from pyams_form.field import Fields
from pyams_form.interfaces import HIDDEN_MODE
from pyams_form.interfaces.form import IAJAXFormRenderer
from pyams_layer.interfaces import IPyAMSLayer
from pyams_utils.adapter import ContextRequestViewAdapter, adapter_config
from pyams_utils.registry import query_utility
from pyams_utils.traversing import get_parent
from pyams_utils.url import absolute_url
from pyams_workflow.interfaces import IWorkflow, IWorkflowCommentInfo, IWorkflowInfo, \
    IWorkflowManagedContent, IWorkflowState, IWorkflowTransitionInfo, IWorkflowVersion, \
    IWorkflowVersions
from pyams_zmi.form import AdminModalAddForm
from pyams_zmi.interfaces import IAdminLayer

__docformat__ = 'restructuredtext'


@ajax_form_config(name='wf-transition.html',
                  context=IWorkflowVersion, layer=IPyAMSLayer)
class WorkflowContentTransitionForm(AdminModalAddForm):
    # pylint: disable=abstract-method
    """Workflow content transition form"""

    prefix = 'workflow.'

    @reify
    def transition(self):
        """Transition property getter"""
        parent = get_parent(self.context, IWorkflowManagedContent)
        workflow = query_utility(IWorkflow, name=parent.workflow_name)
        return workflow.get_transition_by_id(
            self.request.params.get('workflow.widgets.transition_id'))

    @property
    def subtitle(self):
        """Subtitle getter"""
        return self.request.localizer.translate(self.transition.title)

    @property
    def legend(self):
        """Legend getter"""
        return self.request.localizer.translate(self.transition.title)

    fields = Fields(IWorkflowTransitionInfo) + \
        Fields(IWorkflowCommentInfo)

    object_data = {
        'ams-warn-on-change': False
    }

    @property
    def deleted_target(self):
        """Redirect target when current content is deleted"""
        return self.request.root

    @property
    def edit_permission(self):
        return self.transition.permission

    def update(self):
        self.versions = IWorkflowVersions(self.context)
        super().update()

    def update_actions(self):
        super().update_actions()
        add_button = self.actions.get('add')
        if add_button is not None:
            add_button.title = self.request.localizer.translate(self.transition.title)

    def update_widgets(self, prefix=None):
        super().update_widgets(prefix)
        transition_id = self.widgets.get('transition_id')
        if transition_id is not None:
            transition_id.mode = HIDDEN_MODE
            transition_id.value = transition_id.extract()

    def create_and_add(self, data):
        data = data.get(self, data)
        info = IWorkflowInfo(self.context)
        result = info.fire_transition(self.transition.transition_id, comment=data.get('comment'))
        info.fire_automatic()
        IWorkflowState(self.context).state_urgency = data.get('urgent_request') or False
        self.request.registry.notify(ObjectModifiedEvent(self.context))
        return result or info

    def next_url(self):
        return absolute_url(self.context, self.request, 'admin')


@adapter_config(required=(IWorkflowVersion, IAdminLayer, WorkflowContentTransitionForm),
                provides=IAJAXFormRenderer)
class WorkflowContentTransitionFormRenderer(ContextRequestViewAdapter):
    """Workflow content transition form AJAX renderer"""

    def render(self, changes):  # pylint: disable=no-self-use
        """Form changes renderer"""
        if changes is None:
            return None
        if IWorkflowVersion.providedBy(changes):  # new version
            target = changes
        else:
            info = IWorkflowInfo(changes, None)
            if (info is not None) and (info.parent is None):  # deleted version
                versions = self.view.versions
                last_version = versions.get_last_versions()
                if last_version:  # other versions
                    target = last_version[0]
                else:
                    target = self.view.deleted_target
            else:
                target = changes.context
        return {
            'status': 'redirect',
            'location': absolute_url(target, self.request, 'admin')
        }
