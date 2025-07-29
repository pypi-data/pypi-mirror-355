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

"""PyAMS_workflow.content module

This module defines base classes for contents supporting workflows.
"""

from datetime import datetime, timezone

from persistent import Persistent
from pyramid.events import subscriber
from zope.container.contained import Contained
from zope.dublincore.interfaces import IZopeDublinCore
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from pyams_security.interfaces import ISecurityManager
from pyams_security.interfaces.base import PUBLIC_PERMISSION
from pyams_utils.adapter import adapter_config, get_annotation_adapter
from pyams_utils.date import SH_DATE_FORMAT, format_date, format_datetime
from pyams_utils.factory import factory_config, get_object_factory
from pyams_utils.registry import get_utility
from pyams_utils.request import check_request
from pyams_utils.timezone import UTC, gmtime, tztime
from pyams_utils.traversing import get_parent
from pyams_utils.vocabulary import vocabulary_config
from pyams_workflow.interfaces import DISPLAY_CURRENT_VERSION, DISPLAY_FIRST_VERSION, \
    DISPLAY_UNVERSIONED, IObjectClonedEvent, IWorkflow, IWorkflowManagedContent, IWorkflowPublicationInfo, \
    IWorkflowPublicationSupport, IWorkflowState, IWorkflowStateHistoryItem, IWorkflowVersions, \
    PYAMS_CONTENT_PUBLICATION_DATES, VERSION_DISPLAY, VersionError, WORKFLOW_CONTENT_KEY


__docformat__ = 'restructuredtext'

from pyams_workflow import _


@vocabulary_config(name=PYAMS_CONTENT_PUBLICATION_DATES)
class WorkflowContentDisplayedDateVocabulary(SimpleVocabulary):
    """Workflow content displayed date vocabulary"""

    def __init__(self, context):
        request = check_request()
        terms = []
        # check for first version
        first_version_label = request.localizer.translate(DISPLAY_UNVERSIONED)
        versions = IWorkflowVersions(context.__parent__, None)
        if versions is None:
            info = IWorkflowPublicationInfo(context.__parent__, None)            # check for first version
            first_version_label = '{1} (= {0})'.format(
                    first_version_label.lower(),
                    format_date(info.publication_effective_date,
                                format_string=SH_DATE_FORMAT))
            terms.append(SimpleTerm(DISPLAY_FIRST_VERSION, title=first_version_label))
        else:
            try:
                first_version = versions.get_version(1)  # pylint: disable=assignment-from-no-return
            except VersionError:
                pass
            else:
                info = IWorkflowPublicationInfo(first_version, None)
                if info is not None and info.publication_effective_date:
                    first_version_label = '{1} (= {0})'.format(
                        first_version_label.lower(),
                        format_date(info.publication_effective_date,
                                    format_string=SH_DATE_FORMAT))
            terms.append(SimpleTerm(DISPLAY_FIRST_VERSION, title=first_version_label))
        # check for current version
        current_version_label = request.localizer.translate(
            VERSION_DISPLAY[DISPLAY_CURRENT_VERSION])
        info = IWorkflowPublicationInfo(context, None)
        if info is not None and info.publication_effective_date:
            current_version_label = '{1} (= {0})'.format(
                current_version_label.lower(),
                format_date(info.publication_effective_date, format_string=SH_DATE_FORMAT))
        terms.append(SimpleTerm(DISPLAY_CURRENT_VERSION, title=current_version_label))
        super().__init__(terms)


@factory_config(IWorkflowPublicationInfo)
class WorkflowContentPublicationInfo(Persistent, Contained):
    """Workflow content info"""

    _publication_date = FieldProperty(
        IWorkflowPublicationInfo['publication_date'])
    publisher = FieldProperty(
        IWorkflowPublicationInfo['publisher'])
    _first_publication_date = FieldProperty(
        IWorkflowPublicationInfo['first_publication_date'])
    _content_publication_date = FieldProperty(
        IWorkflowPublicationInfo['content_publication_date'])
    _publication_effective_date = FieldProperty(
        IWorkflowPublicationInfo['publication_effective_date'])
    push_end_date = FieldProperty(
        IWorkflowPublicationInfo['push_end_date'])
    _publication_expiration_date = FieldProperty(
        IWorkflowPublicationInfo['publication_expiration_date'])
    displayed_publication_date = FieldProperty(
        IWorkflowPublicationInfo['displayed_publication_date'])

    @property
    def publication_date(self):
        """Publication date getter"""
        return self._publication_date

    @publication_date.setter
    def publication_date(self, value):
        """Publication date setter"""
        self._publication_date = gmtime(value)

    @property
    def publication(self):
        """Publication label used to display workflow publication state"""
        request = check_request()
        translate = request.localizer.translate
        sm = get_utility(ISecurityManager)  # pylint: disable=invalid-name
        return translate(_('{date} by {principal}')).format(
            date=format_datetime(tztime(IWorkflowPublicationInfo(self).publication_date),
                                 request=request),
            principal=translate(sm.get_principal(self.publisher).title))

    @property
    def first_publication_date(self):
        """First publication date getter"""
        return self._first_publication_date

    @property
    def content_publication_date(self):
        """Content first publication date getter"""
        return self._content_publication_date

    @property
    def publication_effective_date(self):
        """Publication effective date getter"""
        return self._publication_effective_date

    @publication_effective_date.setter
    def publication_effective_date(self, value):
        """Publication effective date setter"""
        self._publication_effective_date = value

    def apply_first_publication_date(self):
        """Apply first publication date based on previous publications and effective publication date"""
        dc = IZopeDublinCore(self.__parent__, None)  # pylint: disable=invalid-name
        effective_date = self.publication_effective_date
        if effective_date:
            now = datetime.now(timezone.utc)
            effective_date = max(now, gmtime(effective_date))
            if (self._first_publication_date is None) or \
                    (self._first_publication_date > effective_date):
                self._first_publication_date = effective_date
            if (self._content_publication_date is None) or \
                    (self._content_publication_date > effective_date):
                self._content_publication_date = effective_date
            if dc is not None:
                dc.effective = effective_date
        elif (dc is not None) and dc.effective:
            del dc._mapping['Date.Effective']  # pylint: disable=protected-access

    @property
    def push_end_date_index(self):
        """Push end date getter"""
        value = self.push_end_date or self.publication_expiration_date
        if value is None:
            value = datetime(9999, 12, 31, 23, 59, 59, 999999, UTC)
        return gmtime(value)

    @property
    def publication_expiration_date(self):
        """Publication expiration date getter"""
        return self._publication_expiration_date

    @publication_expiration_date.setter
    def publication_expiration_date(self, value):
        """Publication expiration date setter"""
        value = gmtime(value)
        dc = IZopeDublinCore(self.__parent__, None)  # pylint: disable=invalid-name
        if dc is not None:
            if value:
                dc.expires = value
            elif self._publication_expiration_date:
                del dc._mapping['Date.Expires']  # pylint: disable=protected-access
        self._publication_expiration_date = value

    @property
    def visible_publication_date(self):
        """Visible publication date getter"""
        displayed_date = self.displayed_publication_date
        if displayed_date == DISPLAY_FIRST_VERSION:
            state = IWorkflowState(self.__parent__, None)
            if (state is not None) and (state.version_id > 1):
                versions = IWorkflowVersions(self.__parent__, None)
                if versions is not None:
                    version = versions.get_version(1)  # pylint: disable=assignment-from-no-return
                    return IWorkflowPublicationInfo(version).publication_effective_date
        return self.publication_effective_date

    def reset(self, complete=True):
        """Reset publication dates"""
        self._publication_date = None
        self._first_publication_date = None
        self._publication_effective_date = None
        if complete:
            self._content_publication_date = None
            self._publication_expiration_date = None
            self.push_end_date = None

    def is_published(self, check_parent=True):
        """Check if content is published"""
        # check associated workflow?
        workflow = IWorkflow(self.__parent__, None)
        if workflow is not None:
            if not workflow.visible_states:
                return False
            # check content workflow state
            state = IWorkflowState(self.__parent__, None)
            if state is not None:
                if state.state not in workflow.visible_states:
                    return False
            else:
                versions = IWorkflowVersions(self.__parent__, None)
                if (versions is not None) and not versions.has_version(workflow.visible_states):
                    return False
        # check publication dates
        now = tztime(datetime.now(timezone.utc))
        if not ((self.publication_effective_date is not None) and
                (self.publication_effective_date <= now) and
                ((self.publication_expiration_date is None) or
                 (self.publication_expiration_date >= now))):
            return False
        # check is parent is also published...
        if check_parent:
            parent = get_parent(self.__parent__, IWorkflowPublicationSupport,
                                allow_context=False)
            if (parent is not None) and not IWorkflowPublicationInfo(parent).is_published():
                return False
        return True

    def is_visible(self, request=None, check_parent=True):
        """Check if content is published and visible to given request"""
        if request is None:
            request = check_request()
        # associated workflow?
        content = IWorkflowManagedContent(self.__parent__, None)
        if content is not None:
            wf_name = content.workflow_name
            if not wf_name:
                return True
            # check workflow?
            if content.view_permission and \
               not request.has_permission(content.view_permission, context=self.__parent__):
                return False
        else:
            if not request.has_permission(PUBLIC_PERMISSION, context=self.__parent__):
                return False
        return self.is_published(check_parent)


@adapter_config(required=IWorkflowPublicationSupport,
                provides=IWorkflowPublicationInfo)
def workflow_content_publication_info_factory(context):
    """Workflow content info factory"""
    return get_annotation_adapter(context, WORKFLOW_CONTENT_KEY, IWorkflowPublicationInfo)


@subscriber(IObjectClonedEvent)
def handle_cloned_object(event):
    """Add comment when an object is cloned"""
    request = check_request()
    translate = request.localizer.translate
    source_state = IWorkflowState(event.source)
    factory = get_object_factory(IWorkflowStateHistoryItem)
    if factory is not None:
        item = factory(date=datetime.now(timezone.utc),
                       principal=request.principal.id,
                       comment=translate(_("Clone created from version {source} (in « {state} » "
                                           "state)")).format(
                           source=source_state.version_id,
                           state=translate(
                               IWorkflow(event.source).get_state_label(source_state.state))))
        target_state = IWorkflowState(event.object)
        target_state.history.clear()  # pylint: disable=no-member
        target_state.history.append(item)  # pylint: disable=no-member


@subscriber(IObjectClonedEvent, context_selector=IWorkflowPublicationSupport)
def handle_cloned_publication_support(event):
    """Reset publication info when an object is cloned"""
    IWorkflowPublicationInfo(event.object).reset(complete=False)


@implementer(IWorkflowPublicationInfo)
class HiddenContentPublicationInfo:
    """Hidden content publication info"""

    publication_date = None
    publisher = None
    publication = None
    first_publication_date = None
    content_publication_date = None
    publication_effective_date = None
    publication_expiration_date = None
    visible_publication_date = None
    push_end_date = None
    push_end_date_index = None

    @staticmethod
    def reset(complete=True):  # pylint: disable=unused-argument
        """Reset publication dates"""

    @staticmethod
    def is_published(check_parent=True):  # pylint: disable=unused-argument
        """Check if content is published"""
        return False

    @staticmethod
    def is_visible(request=None, check_parent=True):  # pylint: disable=unused-argument
        """Check if content is published and visible to given request"""
        return False
