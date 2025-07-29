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

"""PyAMS_workflow.zmi.versions module

"""

from pyramid.interfaces import IView
from zope.interface import Interface, implementer

from pyams_layer.interfaces import IPyAMSLayer
from pyams_pagelet.pagelet import pagelet_config
from pyams_security.interfaces.base import VIEW_SYSTEM_PERMISSION
from pyams_security.principal import MissingPrincipal
from pyams_security.utility import get_principal
from pyams_table.column import GetAttrColumn
from pyams_table.interfaces import IColumn, IValues
from pyams_utils.adapter import ContextRequestViewAdapter, adapter_config
from pyams_utils.date import SH_DATETIME_FORMAT
from pyams_utils.text import text_to_html
from pyams_viewlet.viewlet import viewlet_config
from pyams_workflow.interfaces import IWorkflow, IWorkflowState, IWorkflowVersion
from pyams_zmi.interfaces import IAdminLayer
from pyams_zmi.interfaces.viewlet import IContentManagementMenu
from pyams_zmi.table import DateColumn, I18nColumnMixin, Table, TableAdminView
from pyams_zmi.zmi.viewlet.menu import NavigationMenuItem


__docformat__ = 'restructuredtext'

from pyams_workflow import _  # pylint: disable=ungrouped-imports


@viewlet_config(name='workflow-history.menu',
                context=IWorkflowVersion, layer=IAdminLayer,
                manager=IContentManagementMenu, weight=900,
                permission=VIEW_SYSTEM_PERMISSION)
class WorkflowVersionHistoryMenuItem(NavigationMenuItem):
    """Workflow history menu item"""

    label = _("Version history")
    icon_class = 'fas fa-history'
    href = '#version-history.html'


@implementer(IView)
class WorkflowVersionHistoryTable(Table):
    """Workflow version history table"""

    object_data = {
        'responsive': True,
        'auto-width': False,
        'searching': False,
        'length-change': False
    }

    sort_on = None


@adapter_config(required=(IWorkflowVersion, IAdminLayer, WorkflowVersionHistoryTable),
                provides=IValues)
class WorkflowVersionHistoryValuesAdapter(ContextRequestViewAdapter):
    """Workflow version history values adapter"""

    @property
    def values(self):
        """History table getter"""
        yield from IWorkflowState(self.context).history  # pylint: disable=not-an-iterable


@adapter_config(name='date',
                required=(Interface, IAdminLayer, WorkflowVersionHistoryTable),
                provides=IColumn)
class WorkflowVersionHistoryDateColumn(I18nColumnMixin, DateColumn):
    """Workflow version history date column"""

    i18n_header = _("Date")

    attr_name = 'date'
    css_classes = {'td': 'nowrap'}
    weight = 1

    formatter = SH_DATETIME_FORMAT


@adapter_config(name='state',
                required=(Interface, IAdminLayer, WorkflowVersionHistoryTable),
                provides=IColumn)
class WorkflowVersionHistoryStateColumn(I18nColumnMixin, GetAttrColumn):
    """Workflow version history source column"""

    i18n_header = _("New state")

    attr_name = 'target_state'
    weight = 5

    def get_value(self, obj):
        """State column value getter"""
        state = super().get_value(obj)
        workflow = IWorkflow(self.context, None)
        if workflow is None:
            return state
        try:
            term = workflow.states.getTerm(state)
        except LookupError:
            return state or '--'
        else:
            translate = self.request.localizer.translate
            return translate(term.title)


@adapter_config(name='principal',
                required=(Interface, IAdminLayer, WorkflowVersionHistoryTable),
                provides=IColumn)
class WorkflowVersionHistoryPrincipalColumn(I18nColumnMixin, GetAttrColumn):
    """Workflow version history principal column"""

    i18n_header = _("Modifier")

    attr_name = 'principal'
    weight = 10

    def get_value(self, obj):
        """Principal column value getter"""
        principal = get_principal(self.request, obj.principal)
        if isinstance(principal, MissingPrincipal):
            return '--'
        return principal.title


@adapter_config(name='comment',
                required=(Interface, IAdminLayer, WorkflowVersionHistoryTable),
                provides=IColumn)
class WorkflowVersionHistoryCommentColumn(I18nColumnMixin, GetAttrColumn):
    """Workflow version history comment column"""

    i18n_header = _("Comment")

    attr_name = 'comment'
    weight = 15

    def get_value(self, obj):  # pylint: disable=no-self-use
        """Comment column value getter"""
        return text_to_html(obj.comment or '--')


@pagelet_config(name='version-history.html',
                context=IWorkflowVersion, layer=IPyAMSLayer,
                permission=VIEW_SYSTEM_PERMISSION)
class WorkflowVersionHistoryView(TableAdminView):
    """Workflow version history view"""

    @property
    def title(self):
        """Title getter"""
        translate = self.request.localizer.translate  # pylint: disable=no-member
        return translate(_("Version {version} history")).format(
            version=IWorkflowState(self.context).version_id)  # pylint: disable=no-member

    table_class = WorkflowVersionHistoryTable
    table_label = _("History of this version")
