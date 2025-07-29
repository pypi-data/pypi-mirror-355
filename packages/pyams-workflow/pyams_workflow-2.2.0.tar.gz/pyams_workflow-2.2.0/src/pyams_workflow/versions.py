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

"""PyAMS_workflow.versions module

This module defines workflow versions management classes and adapters.
"""

from datetime import datetime, timezone

from persistent import Persistent
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from pyramid.events import subscriber
from zope.component import queryUtility
from zope.container.folder import Folder
from zope.dublincore.interfaces import IZopeDublinCore
from zope.interface import alsoProvides
from zope.location.interfaces import ISublocations
from zope.schema.fieldproperty import FieldProperty
from zope.traversing.interfaces import ITraversable

from pyams_security.interfaces.base import IPrincipalInfo
from pyams_utils.adapter import ContextAdapter, adapter_config, get_annotation_adapter
from pyams_utils.factory import factory_config, get_object_factory
from pyams_utils.registry import get_utility
from pyams_utils.request import check_request, query_request
from pyams_utils.timezone import gmtime
from pyams_utils.traversing import get_parent
from pyams_workflow.interfaces import IWorkflow, IWorkflowManagedContent, IWorkflowState, \
    IWorkflowStateHistoryItem, IWorkflowTransitionEvent, IWorkflowVersion, \
    IWorkflowVersionTransitionEvent, IWorkflowVersions, NONE_STATE, VersionError, \
    WORKFLOW_VERSIONS_KEY, WORKFLOW_VERSION_KEY

__docformat__ = 'restructuredtext'


@factory_config(IWorkflowStateHistoryItem)
class WorkflowHistoryItem(Persistent):
    """Workflow history item"""

    date = FieldProperty(IWorkflowStateHistoryItem['date'])
    source_version = FieldProperty(IWorkflowStateHistoryItem['source_version'])
    source_state = FieldProperty(IWorkflowStateHistoryItem['source_state'])
    target_state = FieldProperty(IWorkflowStateHistoryItem['target_state'])
    transition_id = FieldProperty(IWorkflowStateHistoryItem['transition_id'])
    transition = FieldProperty(IWorkflowStateHistoryItem['transition'])
    principal = FieldProperty(IWorkflowStateHistoryItem['principal'])
    comment = FieldProperty(IWorkflowStateHistoryItem['comment'])

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@factory_config(IWorkflowState)
class WorkflowVersionState(Persistent):
    """Workflow managed content version object"""

    version_id = None
    _state = None
    _state_date = FieldProperty(IWorkflowState['state_date'])
    _state_principal = FieldProperty(IWorkflowState['state_principal'])
    state_urgency = FieldProperty(IWorkflowState['state_urgency'])

    def __init__(self):
        self.history = PersistentList()

    @property
    def state(self):
        """Current state getter"""
        return self._state

    @state.setter
    def state(self, value):
        """State setter"""
        self._state = value
        self._state_date = datetime.now(timezone.utc)
        request = query_request()
        if request is not None:
            self._state_principal = request.principal.id

    @property
    def state_date(self):
        """Getter of state date"""
        return self._state_date

    @property
    def state_principal(self):
        """Getter of state principal"""
        return self._state_principal

    @state_principal.setter
    def state_principal(self, value):
        """Setter of state principal"""
        self._state_principal = value.id if IPrincipalInfo.providedBy(value) else value

    def get_first_state_date(self, states):
        """Getter of first date in given state"""
        for item in self.history:
            if item.target_state in states:
                return item.date
        return None


@adapter_config(required=IWorkflowVersion,
                provides=IWorkflow)
def workflow_version_workflow_factory(context):
    """Workflow content version workflow factory"""
    content = get_parent(context, IWorkflowManagedContent)
    return queryUtility(IWorkflow, name=content.workflow_name)


@adapter_config(required=IWorkflowVersion,
                provides=IWorkflowState)
def workflow_version_state_factory(context):
    """Workflow content version state factory"""
    return get_annotation_adapter(context, WORKFLOW_VERSION_KEY, IWorkflowState)


@subscriber(IWorkflowTransitionEvent)
def handle_workflow_transition(event):
    """Handle workflow transition"""
    if IWorkflowVersionTransitionEvent.providedBy(event):
        return
    principal = event.principal
    factory = get_object_factory(IWorkflowStateHistoryItem)
    if factory is not None:
        item = factory(date=gmtime(datetime.now(timezone.utc)),
                       source_state=event.source,
                       target_state=event.destination,
                       transition_id=event.transition.transition_id,
                       principal=principal.id
                       if IPrincipalInfo.providedBy(principal) else principal,
                       comment=event.comment)
        IWorkflowState(event.object).history.append(item)  # pylint: disable=no-member


@subscriber(IWorkflowVersionTransitionEvent)
def handle_workflow_version_transition(event):
    """Handle workflow version transition"""
    principal = event.principal
    factory = get_object_factory(IWorkflowStateHistoryItem)
    if factory is not None:
        item = factory(date=datetime.now(timezone.utc),
                       source_version=IWorkflowState(event.old_object).version_id,
                       source_state=event.source,
                       target_state=event.destination,
                       transition_id=event.transition.transition_id,
                       principal=principal.id
                       if IPrincipalInfo.providedBy(principal) else principal,
                       comment=event.comment)
        IWorkflowState(event.object).history.append(item)  # pylint: disable=no-member


@factory_config(IWorkflowVersions)
class WorkflowVersions(Folder):
    """Workflow versions adapter"""

    def __init__(self):
        super().__init__()
        self.last_version_id = 0
        self.state_by_version = PersistentMapping()
        self.versions_by_state = PersistentMapping()
        self.deleted = PersistentMapping()

    def get_version(self, version_id=None):
        """Get version with given ID

        If version ID is None or equals -1, method returns the last version.
        """
        if (version_id is None) or (version_id == -1):
            version_id = max(self.state_by_version)
        try:
            return self[str(version_id)]
        except KeyError as ex:  # pylint: disable=invalid-name
            raise VersionError("Missing given version ID {0}".format(version_id)) from ex

    def get_versions(self, states=None, sort=False, reverse=False):
        """Get all versions, or those in given state"""
        if states:
            if isinstance(states, str):
                states = (states, )
            versions = set()
            for state in states:
                if state is None:
                    state = NONE_STATE
                for version in self.versions_by_state.get(state, ()):
                    versions.add(self[str(version)])
            if sort:
                versions = sorted(versions, key=lambda x: int(x.__name__), reverse=reverse)
            return versions
        return (v for k, v in sorted(self.items(), key=lambda x: int(x[0])))

    def get_last_versions(self, count=1):
        """Last version(s) getter"""
        result = list((v for k, v in sorted(self.items(), key=lambda x: -int(x[0]))))
        if count:
            result = result[:count]
        return result

    def add_version(self, content, state, principal=None):
        """Add new version to versions list"""
        self.last_version_id += 1
        version_id = self.last_version_id
        # init version state
        alsoProvides(content, IWorkflowVersion)
        wf_state = IWorkflowState(content)
        wf_state.version_id = version_id
        wf_state.state = state
        if principal is not None:
            wf_state.state_principal = principal
        # store new version
        if state is None:
            state = NONE_STATE
        self[str(version_id)] = content
        self.state_by_version[version_id] = state
        versions = self.versions_by_state.get(state, [])
        versions.append(version_id)
        self.versions_by_state[state] = versions
        return version_id

    def set_state(self, version_id, state, principal=None):
        """Set state of given version"""
        if str(version_id) not in self:
            return
        # update version state
        version = self[str(version_id)]
        wf_state = IWorkflowState(version)
        wf_state.version_id = version_id
        wf_state.state = state
        if principal is not None:
            wf_state.state_principal = principal
        # update versions/states mapping
        if state is None:
            state = NONE_STATE
        old_state = self.state_by_version[version_id]
        versions = self.versions_by_state[old_state]
        if version_id in versions:
            versions.remove(version_id)
            if versions:
                self.versions_by_state[old_state] = versions
            else:
                del self.versions_by_state[old_state]
        self.state_by_version[version_id] = state
        versions = self.versions_by_state.get(state, [])
        versions.append(version_id)
        self.versions_by_state[state] = versions

    def has_version(self, states):
        """Test for existing version(s) in given state(s)"""
        if states is None:
            states = NONE_STATE
        if not isinstance(states, (list, tuple, set)):
            states = {states}
        for state in states:
            if bool(self.versions_by_state.get(state, ())):
                return True
        return False

    def remove_version(self, version_id, state='deleted', comment=None,
                       principal=None, request=None):
        # pylint: disable=too-many-arguments
        """Remove version with given ID"""
        if str(version_id) not in self:
            return
        # update version state
        version = self[str(version_id)]
        wf_state = IWorkflowState(version)
        if comment:
            if request is None:
                request = check_request()
            translate = request.localizer.translate
            workflow = get_utility(IWorkflow,
                                   name=get_parent(self, IWorkflowManagedContent).workflow_name)
            item = WorkflowHistoryItem(date=datetime.now(timezone.utc),
                                       source_version=wf_state.version_id,
                                       source_state=translate(
                                           workflow.states.getTerm(wf_state.state).title),
                                       target_state=translate(
                                           workflow.states.getTerm(state).title),
                                       principal=request.principal.id,
                                       comment=comment)
            wf_state.history.append(item)  # pylint: disable=no-member
        wf_state.state = state
        if principal is not None:
            wf_state.state_principal = principal
        # remove given version
        state = self.state_by_version[version_id]
        versions = self.versions_by_state[state]
        versions.remove(version_id)
        if versions:
            self.versions_by_state[state] = versions
        else:
            del self.versions_by_state[state]
        del self.state_by_version[version_id]
        self.deleted[version_id] = self[str(version_id)]
        del self[str(version_id)]


def get_last_version(content):
    """Helper function used to get last content version"""
    versions = IWorkflowVersions(content, None)
    if versions is None:
        return None
    result = versions.get_last_versions()
    if result:
        return result[0]
    return None


def get_last_version_in_state(content):
    """Helper function used to get last content version in same state"""

    def get_version_order(version):
        """Version sort order getter"""
        dc = IZopeDublinCore(version, None)  # pylint: disable=invalid-name
        if dc is not None:
            return dc.modified
        return int(version.__name__)

    versions = IWorkflowVersions(content, None)
    if versions is not None:
        return sorted(versions.get_versions(IWorkflowState(content).state),
                      key=get_version_order,
                      reverse=True)[0]
    return content


@adapter_config(required=IWorkflowManagedContent,
                provides=IWorkflowVersions)
def workflow_content_versions_factory(context):
    """Workflow versions factory"""
    return get_annotation_adapter(context, WORKFLOW_VERSIONS_KEY, IWorkflowVersions,
                                  name='++versions++')


@adapter_config(required=IWorkflowVersion,
                provides=IWorkflowVersions)
def workflow_version_versions_factory(context):
    """Workflow versions factory for version"""
    parent = get_parent(context, IWorkflowManagedContent)
    if parent is not None:
        return IWorkflowVersions(parent)
    return None


@adapter_config(name='versions',
                required=IWorkflowManagedContent,
                provides=ITraversable)
class WorkflowVersionsTraverser(ContextAdapter):
    """++versions++ namespace traverser"""

    def traverse(self, name, furtherpath=None):  # pylint: disable=unused-argument
        """Versions traverser"""
        versions = IWorkflowVersions(self.context)
        if name:
            return versions[name]
        return versions


@adapter_config(name='versions',
                required=IWorkflowManagedContent,
                provides=ISublocations)
class WorkflowVersionsSublocations(ContextAdapter):
    """Workflow versions sub-locations"""

    def sublocations(self):
        """Versions sub-locations getter"""
        yield from IWorkflowVersions(self.context).values()
