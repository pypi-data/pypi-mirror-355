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

"""PyAMS workflow.interfaces module

This module defines package public interfaces.
"""

from zope.annotation import IAttributeAnnotatable
from zope.interface import Attribute, Interface, Invalid, implementer, invariant
from zope.interface.interfaces import IObjectEvent, ObjectEvent
from zope.lifecycleevent import IObjectCreatedEvent, ObjectCreatedEvent
from zope.schema import Bool, Choice, Datetime, Int, List, Object, Set, Text, TextLine
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from pyams_security.interfaces.base import PUBLIC_PERMISSION
from pyams_security.schema import PrincipalField


from pyams_workflow import _


#
# Transitions interfaces
#

MANUAL_TRANSITION = 0
"""Manual transition trigger ID"""

AUTOMATIC_TRANSITION = 1
"""Automatic transition trigger ID"""

SYSTEM_TRANSITION = 2
"""System transition trigger ID"""


NONE_STATE = '__none__'
"""Unknown state identifier"""

DELETED_STATE = 'deleted'
"""Deleted target state"""


class InvalidTransitionError(Exception):
    """Base transition error"""

    def __init__(self, source):  # pylint: disable=super-init-not-called
        self.source = source

    def __str__(self):
        return 'source: "%s"' % self.source


class NoTransitionAvailableError(InvalidTransitionError):
    """Exception raised when there is not available transition"""

    def __init__(self, source, destination):
        super().__init__(source)
        self.destination = destination

    def __str__(self):
        return 'source: "%s" destination: "%s"' % (self.source, self.destination)


class AmbiguousTransitionError(InvalidTransitionError):
    """Exception raised when required transition is ambiguous"""

    def __init__(self, source, destination):
        super().__init__(source)
        self.destination = destination

    def __str__(self):
        return 'source: "%s" destination: "%s"' % (self.source, self.destination)


class VersionError(Exception):
    """Versions management error"""


class ConditionFailedError(Exception):
    """Exception raised when transition condition failed"""


class IWorkflowTransitionEvent(IObjectEvent):
    """Workflow transition event interface"""

    workflow = Attribute("Workflow utility")

    principal = Attribute("Event principal")

    source = Attribute('Original state or None if initial state')

    destination = Attribute('New state')

    transition = Attribute('Transition that was fired or None if initial state')

    comment = Attribute('Comment that went with state transition')


@implementer(IWorkflowTransitionEvent)
class WorkflowTransitionEvent(ObjectEvent):
    """Workflow transition event"""

    def __init__(self, obj, workflow, principal, source, destination, transition, comment):
        # pylint: disable=too-many-arguments
        super().__init__(obj)
        self.workflow = workflow
        self.principal = principal
        self.source = source
        self.destination = destination
        self.transition = transition
        self.comment = comment


class IWorkflowVersionTransitionEvent(IWorkflowTransitionEvent):
    """Workflow version transition event interface"""

    old_object = Attribute('Old version of object')


@implementer(IWorkflowVersionTransitionEvent)
class WorkflowVersionTransitionEvent(WorkflowTransitionEvent):
    """Workflow version transition event"""

    def __init__(self, obj, workflow, principal, old_object,
                 source, destination, transition, comment):
        # pylint: disable=too-many-arguments
        super().__init__(obj, workflow, principal, source, destination, transition, comment)
        self.old_object = old_object


class IWorkflowTransitionInfo(Interface):
    """Workflow transition info

    This interface is actually used to provide transition ID in
    workflow management forms.
    """

    transition_id = TextLine(title=_("Transition ID"),
                             required=True)


class IObjectClonedEvent(IObjectCreatedEvent):
    """Object cloned event interface"""

    source = Attribute("Cloned object source")


@implementer(IObjectClonedEvent)
class ObjectClonedEvent(ObjectCreatedEvent):
    """Object cloned event"""

    def __init__(self, obj, source):
        super().__init__(obj)
        self.source = source


#
# Main workflow interface
#

class IWorkflow(Interface):
    """Workflow utility interface.

    A workflow is a "state machine" defined by a set of states and transitions.
    """

    label = Attribute("Workflow label")

    initial_state = Attribute("Initial state")

    update_states = Set(title="Updatable states",
                        description="States of contents which are updatable by standard "
                                    "contributors")

    readonly_states = Set(title="Read-only states",
                          description="States of contents which can't be modified by anybody")

    protected_states = Set(title="Protected states",
                           description="States of contents which can only be modified by site "
                                       "administrators")

    manager_states = Set(title="Manager states",
                         description="States of contents which can be modified by site "
                                     "administrators and content managers")

    published_states = Set(title="Published states",
                           description="States of contents which are published")

    visible_states = Set(title="Visible states",
                         description="States of contents which are visible in front-office")

    waiting_states = Set(title="Waiting states",
                         description="States of contents waiting for action")

    retired_states = Set(title="Retired states",
                         description="States of contents which are retired but not yet archived")

    archived_states = Set(title="Archived states",
                          description="States of contents which are archived and can't be "
                                      "updated anymore")

    auto_retired_state = Attribute("Auto-retired state")

    def initialize(self):
        """Do any needed initialization.

        Such as initialization with the workflow versions system.
        """

    def refresh(self, transitions):
        """Refresh workflow completely with new transitions."""

    def get_state_label(self, state):
        """Get given state label"""

    def get_transitions(self, source):
        """Get all transitions from source"""

    def get_transition(self, source, transition_id):
        """Get transition with transition_id given source state.

        If the transition is invalid from this source state,
        an InvalidTransitionError is raised.
        """

    def get_transition_by_id(self, transition_id):
        """Get transition with transition_id"""


WORKFLOWS_VOCABULARY = 'PyAMS_workflow.workflows'
"""Workflows vocabulary name"""


#
# Content workflow management interface
#

class IWorkflowInfo(Interface):
    """Get workflow info about workflow object, and drive workflow.

    Defined as a dynamic adapter, no workflow related information should
    be stored for this interface..
    """

    def set_initial_state(self, state, comment=None):
        """Set initial state for the context object.

        Fires a transition event.
        """

    # pylint: disable=too-many-arguments
    def fire_transition(self, transition_id, comment=None, side_effect=None,
                        check_security=True, principal=None, request=None):
        """Fire a transition for the context object.

        There's an optional comment parameter that contains some
        opaque object that offers a comment about the transition.
        This is useful for manual transitions where users can motivate
        their actions.

        There's also an optional side effect parameter which should
        be a callable which receives the object undergoing the transition
        as the parameter. This could do an editing action of the newly
        transitioned workflow object before an actual transition event is
        fired.

        If check_security is set to False, security is not checked
        and an application can fire a transition no matter what the
        user's permission is.
        """

    # pylint: disable=too-many-arguments
    def fire_transition_toward(self, state, comment=None, side_effect=None,
                               check_security=True, principal=None, request=None):
        """Fire transition toward state.

        Looks up a manual transition that will get to the indicated
        state.

        If no such transition is possible, NoTransitionAvailableError will
        be raised.

        If more than one manual transitions are possible,
        AmbiguousTransitionError will be raised.
        """

    # pylint: disable=too-many-arguments
    def fire_transition_for_versions(self, state, transition_id, comment=None,
                                     principal=None, request=None):
        """Fire a transition for all versions in a state"""

    def fire_automatic(self):
        """Fire automatic transitions if possible by condition"""

    def has_version(self, state):
        """Return true if a version exists in given state"""

    def get_manual_transition_ids(self):
        """Returns list of valid manual transitions.

        These transitions have to have a condition that's True.
        """

    def get_manual_transition_ids_toward(self, state):
        """Returns list of manual transitions towards state"""

    def get_automatic_transition_ids(self):
        """Returns list of possible automatic transitions.

        Condition is not checked.
        """

    def has_automatic_transitions(self):
        """Return true if there are possible automatic outgoing transitions.

        Condition is not checked.
        """


#
# Workflow state interfaces
#

class IWorkflowStateHistoryItem(Interface):
    """Workflow state history item

    Each applied transition is stored into content history.
    """

    date = Datetime(title="State change datetime",
                    required=True)

    source_version = Int(title="Source version ID",
                         required=False)

    source_state = TextLine(title="Transition source state",
                            required=False)

    target_state = TextLine(title="Transition target state",
                            required=True)

    transition_id = TextLine(title="Transition ID",
                             required=True)

    transition = TextLine(title="Transition name",
                          required=True)

    principal = PrincipalField(title="Transition principal",
                               required=False)

    comment = Text(title="Transition comment",
                   required=False)


WORKFLOW_STATE_KEY = 'pyams_workflow.state'
"""Annotations key used to store workflow state"""


class IWorkflowState(Interface):
    """Store state on workflow object.

    Defined as an adapter.
    """

    version_id = Int(title=_("Version ID"))

    state = TextLine(title=_("Version state"))

    state_date = Datetime(title=_("State date"),
                          description=_("Date at which the current state was applied"))

    state_principal = PrincipalField(title=_("State principal"),
                                     description=_("ID of the principal which defined current "
                                                   "state"))

    state_urgency = Bool(title=_("Urgent request?"),
                         required=True,
                         default=False)

    history = List(title="Workflow states history",
                   value_type=Object(schema=IWorkflowStateHistoryItem))

    def get_first_state_date(self, states):
        """Get first date at which given state was set"""


#
# Versions management interfaces
#

WORKFLOW_VERSIONS_KEY = 'pyams_workflow.versions'
"""Annotations key used to store versions information"""


class IWorkflowVersions(Interface):
    """Interface to get information about versions of content in workflow"""

    last_version_id = Attribute("Last version ID")

    def get_version(self, version_id=None):
        """Get version matching given id

        If version ID is None or equals -1, method returns the last version.
        """

    def get_versions(self, states=None, sort=False, reverse=False):
        """Get all versions of object known for this (optional) state"""

    def get_last_versions(self, count=1):
        """Get last versions of this object. Set count=0 to get all versions."""

    def add_version(self, content, state, principal=None):
        """Return new unique version id"""

    def set_state(self, version_id, state, principal=None):
        """Set new state for given version"""

    def has_version(self, state):
        """Return true if a version exists with the specific workflow state"""

    # pylint: disable=too-many-arguments
    def remove_version(self, version_id, state=DELETED_STATE, comment=None,
                       principal=None, request=None):
        """Remove version with given ID"""


class IWorkflowStateLabel(Interface):
    """Workflow state label adapter interface"""

    # pylint: disable=redefined-builtin
    def get_label(self, content, request=None, format=True):
        """Get state label for given content"""


#
# Content workflow support interfaces
#

class IWorkflowManagedContent(IAttributeAnnotatable):
    """Workflow managed content"""

    content_class = Attribute("Content class")

    workflow_name = Choice(title=_("Workflow name"),
                           description=_("Name of workflow utility managing this content"),
                           required=True,
                           vocabulary=WORKFLOWS_VOCABULARY)

    view_permission = Choice(title=_("View permission"),
                             description=_("This permission will be required to display content"),
                             vocabulary='PyAMS permissions',
                             default=PUBLIC_PERMISSION,
                             required=False)


DISPLAY_FIRST_VERSION = 'first'
"""Displayed publication date is the first publication date"""

DISPLAY_CURRENT_VERSION = 'current'
"""Displayed publication date is the publication date of the current version"""

VERSION_DISPLAY = {
    DISPLAY_FIRST_VERSION: _("Display first version date"),
    DISPLAY_CURRENT_VERSION: _("Display current version date")
}

DISPLAY_UNVERSIONED = _("Display content publication date")


VERSION_DISPLAY_VOCABULARY = SimpleVocabulary([
    SimpleTerm(v, title=t) for v, t in VERSION_DISPLAY.items()
])

PYAMS_CONTENT_PUBLICATION_DATES = 'PyAMS_workflow.content.publication_date'
"""Publication dates vocabulary name"""

WORKFLOW_CONTENT_KEY = 'pyams_workflow.content_info'
"""Annotations key used to store content publication information"""


class IWorkflowPublicationInfo(Interface):
    """Workflow content publication info

    This interface is used to specify publication dates applied on a
    given content.
    """

    publication_date = Datetime(title=_("Publication date"),
                                description=_("Last date at which content was accepted for "
                                              "publication"),
                                required=False)

    publisher = PrincipalField(title=_("Publisher"),
                               description=_("Name of the manager who published the document"),
                               required=False)

    publication = TextLine(title=_("Publication"),
                           description=_("Last publication date and actor"),
                           required=False,
                           readonly=True)

    first_publication_date = Datetime(title=_("First version publication date"),
                                      description=_("First date at which content version "
                                                    "was accepted for publication"),
                                      required=False)

    content_publication_date = Datetime(title=_("First content publication date"),
                                        description=_("First date at which first content version "
                                                      "was accepted for publication"),
                                        required=False)

    publication_effective_date = Datetime(title=_("Publication start date"),
                                          description=_("Date from which content will be "
                                                        "visible"),
                                          required=False)

    def apply_first_publication_date(self):
        """Apply first publication date based on previous publications and effective publication date"""
        
    push_end_date = Datetime(title=_("Push end date"),
                             description=_("Some contents can be pushed by components to "
                                           "front-office pages; if you set a date here, this "
                                           "content will not be pushed anymore passed this "
                                           "date, but will still be available via search engine "
                                           "or direct links"),
                             required=False)

    push_end_date_index = Attribute("Push end date value used by catalog indexes")

    @invariant
    def check_push_end_date(self):
        """Check push end date"""
        if self.push_end_date is not None:
            if self.publication_effective_date is None:
                raise Invalid(_("Can't define push end date without publication start date!"))
            if self.publication_effective_date >= self.push_end_date:
                raise Invalid(_("Push end date must be defined after publication start date!"))
            if self.publication_expiration_date is not None:
                if self.publication_expiration_date < self.push_end_date:
                    raise Invalid(_("Push end date must be null or defined before publication "
                                    "end date!"))

    publication_expiration_date = Datetime(title=_("Publication end date"),
                                           description=_("Date past which content will not be "
                                                         "visible"),
                                           required=False)

    @invariant
    def check_expiration_date(self):
        """Check expiration date"""
        if self.publication_expiration_date is not None:
            if self.publication_effective_date is None:
                raise Invalid(_("Can't define publication end date without publication "
                                "start date!"))
            if self.publication_effective_date >= self.publication_expiration_date:
                raise Invalid(_("Publication end date must be defined after publication "
                                "start date!"))

    displayed_publication_date = Choice(title=_("Displayed publication date"),
                                        description=_("The matching date will be displayed in "
                                                      "front-office"),
                                        vocabulary=PYAMS_CONTENT_PUBLICATION_DATES,
                                        default=DISPLAY_FIRST_VERSION,
                                        required=True)

    visible_publication_date = Attribute("Visible publication date")

    def reset(self, complete=True):
        """Reset all publication info (used by clone features)

        If 'complete' argument is True, all date fields are reset; otherwise, push and
        publication end dates are preserved in new versions.
        """

    def is_published(self, check_parent=True):
        """Is the content published?"""

    def is_visible(self, request=None, check_parent=True):
        """Is the content visible?"""


class IWorkflowPublicationSupport(IAttributeAnnotatable):
    """Workflow publication support"""


WORKFLOW_VERSION_KEY = 'pyams_workflow.version'
"""Annotations key used to store version information"""


class IWorkflowVersion(IWorkflowPublicationSupport):
    """Workflow content version marker interface"""


#
# User content workflow interfaces
#

class IWorkflowRequestUrgencyInfo(Interface):
    """Workflow request urgency info"""

    urgent_request = Bool(title=_("Urgent request?"),
                          description=_("Please use this option only when really needed..."),
                          required=True,
                          default=False)


class IWorkflowCommentInfo(Interface):
    """Workflow comment info"""

    comment = Text(title=_("Comment"),
                   description=_("Comment associated with this operation"),
                   required=False)
