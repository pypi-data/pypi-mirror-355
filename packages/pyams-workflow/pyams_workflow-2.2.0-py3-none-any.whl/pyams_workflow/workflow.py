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

"""PyAMS_workflow.workflow module

This module defines main workflow management utility.
"""

from pyramid.httpexceptions import HTTPUnauthorized
from zope.component import getUtilitiesFor
from zope.interface import implementer
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from pyams_security.interfaces.base import IPrincipalInfo
from pyams_utils.adapter import adapter_config
from pyams_utils.registry import get_utility
from pyams_utils.request import check_request
from pyams_utils.traversing import get_parent
from pyams_utils.vocabulary import vocabulary_config
from pyams_workflow.interfaces import AUTOMATIC_TRANSITION, AmbiguousTransitionError, \
    ConditionFailedError, IWorkflow, IWorkflowInfo, IWorkflowManagedContent, IWorkflowState, \
    IWorkflowVersion, IWorkflowVersions, InvalidTransitionError, MANUAL_TRANSITION, \
    NoTransitionAvailableError, SYSTEM_TRANSITION, WORKFLOWS_VOCABULARY, \
    WorkflowTransitionEvent, WorkflowVersionTransitionEvent


__docformat__ = 'restructuredtext'

from pyams_workflow import _


def NullCondition(wf, context):  # pylint: disable=invalid-name,unused-argument
    """Null condition"""
    return True


def NullAction(wf, context):  # pylint: disable=invalid-name,unused-argument
    """Null action"""


def granted_permission(permission, context):  # pylint: disable=unused-argument
    """Automatically granted permission"""
    return True


class Transition:  # pylint: disable=too-many-instance-attributes
    """Transition object

    A transition doesn't make anything by itself.
    Everything is handled by the workflow utility
    """

    def __init__(self, transition_id, title, source, destination,  # pylint: disable=too-many-arguments
                 condition=NullCondition,
                 action=NullAction,
                 trigger=MANUAL_TRANSITION,
                 permission=None,
                 order=0,
                 **user_data):
        self.transition_id = transition_id
        self.title = title
        self.source = source
        self.destination = destination
        self.condition = condition
        self.action = action
        self.trigger = trigger
        self.permission = permission
        self.order = order
        self.user_data = user_data


@implementer(IWorkflow)
class Workflow:  # pylint: disable=too-many-instance-attributes
    """Workflow utility base class"""

    label = None

    def __init__(self, transitions, states,  # pylint: disable=too-many-arguments
                 initial_state=None,
                 update_states=None,
                 readonly_states=None,
                 protected_states=None,
                 manager_states=None,
                 published_states=None,
                 visible_states=None,
                 waiting_states=None,
                 retired_states=None,
                 archived_states=None,
                 auto_retired_state=None):
        self.refresh(transitions)
        self.states = states
        self.initial_state = initial_state
        self.update_states = set(update_states or ())
        self.readonly_states = set(readonly_states or ())
        self.protected_states = set(protected_states or ())
        self.manager_states = set(manager_states or ())
        self.published_states = set(published_states or ())
        self.visible_states = set(visible_states) if visible_states else self.published_states
        self.waiting_states = set(waiting_states or ())
        self.retired_states = set(retired_states or ())
        self.archived_states = set(archived_states or ())
        self.auto_retired_state = auto_retired_state

    def _register(self, transition):
        transitions = self._sources.setdefault(transition.source, {})
        transitions[transition.transition_id] = transition
        self._id_transitions[transition.transition_id] = transition

    def refresh(self, transitions):
        """Reset workflow transitions list"""
        self._sources = {}
        self._id_transitions = {}
        for transition in transitions:
            self._register(transition)

    def get_state_label(self, state):
        """Get label matching given state"""
        try:
            return self.states.getTerm(state).title
        except LookupError:
            return _('-- unknown --')

    def get_transitions(self, source):
        """Get transitions from given source state"""
        try:
            return self._sources[source].values()
        except KeyError:
            return []

    def get_transition(self, source, transition_id):
        """Get transition with given ID from given source state"""
        transition = self._id_transitions[transition_id]
        if transition.source != source:
            raise InvalidTransitionError(source)
        return transition

    def get_transition_by_id(self, transition_id):
        """Get transition with given ID"""
        return self._id_transitions[transition_id]


@adapter_config(required=IWorkflowVersion,
                provides=IWorkflowInfo)
class WorkflowInfo:
    """Workflow info adapter"""

    def __init__(self, context):
        self.context = context
        self.wf = get_utility(IWorkflow, name=self.name)  # pylint: disable=invalid-name

    @property
    def parent(self):
        """Workflow managed content getter"""
        return get_parent(self.context, IWorkflowManagedContent)

    @property
    def name(self):
        """Workflow name getter"""
        return self.parent.workflow_name

    def fire_transition(self, transition_id, comment=None, side_effect=None,
                        check_security=True, principal=None, request=None):
        # pylint: disable=too-many-arguments
        """Fire transition with given ID"""
        versions = IWorkflowVersions(self.parent)
        state = IWorkflowState(self.context)
        if request is None:
            principal_id = principal.id if IPrincipalInfo.providedBy(principal) else principal
            request = check_request(principal_id=principal_id)
        # this raises InvalidTransitionError if id is invalid for current state
        transition = self.wf.get_transition(state.state, transition_id)
        # check whether we may execute this workflow transition
        if (check_security and
                transition.permission and
                not request.has_permission(transition.permission, context=self.context)):
            raise HTTPUnauthorized()
        # now make sure transition can still work in this context
        if not transition.condition(self, self.context):
            raise ConditionFailedError()
        # perform action, return any result as new version
        if principal is None:
            principal = request.principal
        result = transition.action(self, self.context)
        if result is not None:
            # stamp it with version
            versions.add_version(result, transition.destination, principal)
            # execute any side effect:
            if side_effect is not None:
                side_effect(result)
            event = WorkflowVersionTransitionEvent(result, self.wf, principal, self.context,
                                                   transition.source,
                                                   transition.destination,
                                                   transition, comment)
        else:
            versions.set_state(state.version_id, transition.destination, principal)
            # execute any side effect
            if side_effect is not None:
                side_effect(self.context)
            event = WorkflowTransitionEvent(self.context, self.wf, principal,
                                            transition.source,
                                            transition.destination,
                                            transition, comment)
        # change state of context or new object
        registry = request.registry
        registry.notify(event)
        # send modified event for original or new object
        if result is None:
            registry.notify(ObjectModifiedEvent(self.context))
        else:
            registry.notify(ObjectModifiedEvent(result))
        return result

    def fire_transition_toward(self, state, comment=None, side_effect=None,
                               check_security=True, principal=None, request=None):
        # pylint: disable=too-many-arguments
        """Fire transition(s) to given state"""
        current_state = IWorkflowState(self.context)
        if state == current_state.state:  # unchanged state
            return None
        transition_ids = self.get_fireable_transition_ids_toward(state, check_security)
        if not transition_ids:
            raise NoTransitionAvailableError(current_state.state, state)
        if len(transition_ids) != 1:
            raise AmbiguousTransitionError(current_state.state, state)
        return self.fire_transition(transition_ids[0], comment, side_effect,
                                    check_security, principal, request)

    def fire_transition_for_versions(self, state, transition_id, comment=None,
                                     principal=None, request=None):
        # pylint: disable=too-many-arguments
        """Fire transition for all versions in given state"""
        versions = IWorkflowVersions(self.parent)
        for version in versions.get_versions(state):
            IWorkflowInfo(version).fire_transition(transition_id, comment,
                                                   principal=principal, request=request)

    def fire_automatic(self):
        """Fire automatic transitions"""
        for transition_id in self.get_automatic_transition_ids():
            try:
                self.fire_transition(transition_id)
            except ConditionFailedError:
                # if condition failed, that's fine, then we weren't
                # ready to fire yet
                pass
            else:
                # if we actually managed to fire a transition,
                # we're done with this one now.
                return

    def has_version(self, state):
        """Test for existing versions in given state"""
        wf_versions = IWorkflowVersions(self.parent)
        return wf_versions.has_version(state)

    def get_manual_transition_ids(self, check_security=True):
        """Getter for available transitions IDs"""
        if check_security:
            request = check_request()
            permission_checker = request.has_permission
        else:
            permission_checker = granted_permission
        return [
            transition.transition_id
            for transition in sorted(self._get_transitions(MANUAL_TRANSITION),
                                     key=lambda x: x.user_data.get('order', 999))
            if transition.condition(self, self.context) and permission_checker(
                transition.permission, context=self.context)
        ]

    def get_system_transition_ids(self):
        """Getter for system transitions IDs, ignoring permissions checks.
        """
        return [
            transition.transition_id
            for transition in sorted(self._get_transitions(SYSTEM_TRANSITION),
                                     key=lambda x: x.user_data.get('order', 999))
            if transition.condition(self, self.context)
        ]

    def get_fireable_transition_ids(self, check_security=True):
        """Get IDs of transitions which can be fired"""
        return (self.get_manual_transition_ids(check_security) +
                self.get_system_transition_ids())

    def get_fireable_transition_ids_toward(self, state, check_security=True):
        """Get IDs of transitions which can be fired to access given state"""
        result = []
        for transition_id in self.get_fireable_transition_ids(check_security):
            transition = self.wf.get_transition_by_id(transition_id)
            if transition.destination == state:
                result.append(transition_id)
        return result

    def get_automatic_transition_ids(self):
        """Get IDs of automatic transitions"""
        return [
            transition.transition_id
            for transition in self._get_transitions(AUTOMATIC_TRANSITION)
        ]

    def has_automatic_transitions(self):
        """Text existing automatic transitions"""
        return bool(self.get_automatic_transition_ids())

    def _get_transitions(self, trigger):
        """Retrieve all possible transitions from workflow utility"""
        state = IWorkflowState(self.context)
        transitions = self.wf.get_transitions(state.state)
        # now filter these transitions to retrieve all possible
        # transitions in this context, and return their ids
        return [transition for transition in transitions if transition.trigger == trigger]


@vocabulary_config(name=WORKFLOWS_VOCABULARY)
class WorkflowsVocabulary(SimpleVocabulary):
    """Workflows vocabulary"""

    interface = IWorkflow

    def __init__(self, context, **kw):
        terms = [
            SimpleTerm(name, title=util.label)
            for name, util in getUtilitiesFor(self.interface, context)
        ]
        super().__init__(terms)
