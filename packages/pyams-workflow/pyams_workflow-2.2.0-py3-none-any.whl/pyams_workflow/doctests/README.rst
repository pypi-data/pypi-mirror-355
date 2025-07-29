======================
PyAMS workflow package
======================


Introduction
------------

This package is composed of a set of utility functions, usable into any Pyramid application.

    >>> import pprint

    >>> from pyramid.testing import setUp, tearDown, DummyRequest
    >>> config = setUp(hook_zca=True)
    >>> config.registry.settings['zodbconn.uri'] = 'memory://'

    >>> from beaker.cache import CacheManager, cache_regions
    >>> cache = CacheManager(**{'cache.type': 'memory'})
    >>> cache_regions.update({'short': {'type': 'memory', 'expire': 10}})
    >>> cache_regions.update({'default': {'type': 'memory', 'expire': 60}})
    >>> cache_regions.update({'long': {'type': 'memory', 'expire': 600}})

    >>> from pyramid_zodbconn import includeme as include_zodbconn
    >>> include_zodbconn(config)
    >>> from cornice import includeme as include_cornice
    >>> include_cornice(config)
    >>> from pyams_utils import includeme as include_utils
    >>> include_utils(config)
    >>> from pyams_site import includeme as include_site
    >>> include_site(config)
    >>> from pyams_security import includeme as include_security
    >>> include_security(config)
    >>> from pyams_form import includeme as include_form
    >>> include_form(config)
    >>> from pyams_skin import includeme as include_skin
    >>> include_skin(config)
    >>> from pyams_zmi import includeme as include_zmi
    >>> include_zmi(config)
    >>> from pyams_workflow import includeme as include_workflow
    >>> include_workflow(config)

    >>> from pyams_utils.registry import get_utility, set_local_registry
    >>> registry = config.registry
    >>> set_local_registry(registry)

    >>> from pyams_security.principal import PrincipalInfo
    >>> request = DummyRequest(principal=PrincipalInfo(id='admin:admin'))

    >>> from pyams_site.generations import upgrade_site
    >>> app = upgrade_site(request)
    Upgrading PyAMS timezone to generation 1...
    Upgrading PyAMS security to generation 2...

    >>> from pyramid.threadlocal import manager
    >>> manager.push({'registry': config.registry, 'request': request})

    >>> from zope.traversing.interfaces import BeforeTraverseEvent
    >>> from pyams_utils.registry import handle_site_before_traverse
    >>> handle_site_before_traverse(BeforeTraverseEvent(app, request))


Creating a first workflow
-------------------------

We are going to create a simple workflow with four states which are 'draft', 'published',
'archived' and 'deleted'.

    >>> from pyams_workflow.interfaces import IWorkflow
    >>> class IBasicWorkflow(IWorkflow):
    ...     """PyAMS basic workflow marker interface"""

    >>> DRAFT = 'draft'
    >>> PUBLISHED = 'published'
    >>> ARCHIVED = 'archived'
    >>> DELETED = 'deleted'

    >>> STATES_IDS = (DRAFT,
    ...               PUBLISHED,
    ...               ARCHIVED,
    ...               DELETED)

    >>> STATES_LABELS = ("Draft", "Published", "Archived", "Deleted")

    >>> from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
    >>> STATES_VOCABULARY = SimpleVocabulary([SimpleTerm(STATES_IDS[i], title=t)
    ...                                       for i, t in enumerate(STATES_LABELS)])

    >>> STATES_HEADERS = {
    ...     DRAFT: "draft created",
    ...     PUBLISHED: "published",
    ...     ARCHIVED: "archived"
    ... }

    >>> PUBLISH_CONTENT_PERMISSION = 'pyams.PublishContent'
    >>> CREATE_VERSION_PERMISSION = 'pyams.CreateVersion'

We can now initialize a list of transitions:

    >>> from pyams_utils.request import check_request
    >>> def can_manage_content(wf, context):
    ...     return True

    >>> def can_create_new_version(wf, context):
    ...     versions = IWorkflowVersions(context)
    ...     if versions.has_version(DRAFT):
    ...         return False
    ...     return True

    >>> def can_delete_version(wf, context):
    ...     return True

    >>> from datetime import datetime, timedelta, timezone
    >>> from pyams_workflow.interfaces import IWorkflowPublicationInfo
    >>> def publish_action(wf, context):
    ...     """Publish version"""
    ...     request = check_request(principal_id='admin:admin')
    ...     publication_info = IWorkflowPublicationInfo(context)
    ...     publication_info.publication_date = datetime.now(timezone.utc)
    ...     publication_info.publisher = request.principal.id
    ...     publication_info.apply_first_publication_date()
    ...     version_id = IWorkflowState(context).version_id
    ...     for version in IWorkflowVersions(context).get_versions((PUBLISHED, )):
    ...         if version is not context:
    ...             IWorkflowInfo(version).fire_transition_toward(ARCHIVED,
    ...                                                           comment="Published version {0}".format(
    ...                                                               version_id),
    ...                                                           request=request)

    >>> from zope.copy import copy
    >>> from zope.location import locate
    >>> from pyams_utils.registry import get_pyramid_registry
    >>> from pyams_workflow.interfaces import ObjectClonedEvent

    >>> def clone_action(wf, context):
    ...     """Create new version"""
    ...     result = copy(context)
    ...     locate(result, context.__parent__)
    ...     registry = get_pyramid_registry()
    ...     registry.notify(ObjectClonedEvent(result, context))
    ...     return result

    >>> def delete_action(wf, context):
    ...     """Delete draft version"""
    ...     versions = IWorkflowVersions(context)
    ...     versions.remove_version(IWorkflowState(context).version_id,
    ...                             principal=request.principal,
    ...                             comment="Version deleted")

    >>> from pyams_security.interfaces.base import FORBIDDEN_PERMISSION
    >>> from pyams_workflow.workflow import granted_permission, Transition
    >>> init = Transition(transition_id='init',
    ...                   title="Initialize",
    ...                   source=None,
    ...                   destination=DRAFT,
    ...                   history_label="Draft creation")

    >>> draft_to_published = Transition(transition_id='draft_to_published',
    ...                                 title="Publish",
    ...                                 source=DRAFT,
    ...                                 destination=PUBLISHED,
    ...                                 condition=can_manage_content,
    ...                                 action=publish_action,
    ...                                 history_label="Content published",
    ...                                 order=1)

    >>> published_to_archived = Transition(transition_id='published_to_archived',
    ...                                    title="Archive content",
    ...                                    source=PUBLISHED,
    ...                                    destination=ARCHIVED,
    ...                                    permission=FORBIDDEN_PERMISSION,
    ...                                    condition=can_manage_content,
    ...                                    history_label="Content archived",
    ...                                    order=2)

    >>> published_to_draft = Transition(transition_id='published_to_draft',
    ...                                 title="Create new version",
    ...                                 source=PUBLISHED,
    ...                                 destination=DRAFT,
    ...                                 condition=can_create_new_version,
    ...                                 action=clone_action,
    ...                                 history_label="New version created",
    ...                                 order=3)

    >>> archived_to_draft = Transition(transition_id='archived_to_draft',
    ...                                title="Create new version",
    ...                                source=ARCHIVED,
    ...                                destination=DRAFT,
    ...                                condition=can_create_new_version,
    ...                                action=clone_action,
    ...                                history_label="New version created",
    ...                                order=4)

    >>> delete = Transition(transition_id='delete',
    ...                     title="Delete version",
    ...                     source=DRAFT,
    ...                     destination=DELETED,
    ...                     condition=can_delete_version,
    ...                     action=delete_action,
    ...                     menu_icon_class='fab fa-trash',
    ...                     menu_divider=True,
    ...                     history_label="Version deleted",
    ...                     order=99)

    >>> wf_transitions = {init,
    ...                   draft_to_published,
    ...                   published_to_archived,
    ...                   published_to_draft,
    ...                   archived_to_draft,
    ...                   delete}

    >>> from zope.interface import implementer
    >>> from pyams_workflow.workflow import Workflow

    >>> @implementer(IBasicWorkflow)
    ... class BasicWorkflow(Workflow):
    ...     """PyAMS basic workflow"""

    >>> wf = BasicWorkflow(wf_transitions,
    ...                    states=STATES_VOCABULARY,
    ...                    initial_state=DRAFT,
    ...                    update_states=(DRAFT,),
    ...                    readonly_states=(PUBLISHED, ARCHIVED),
    ...                    protected_states=(PUBLISHED, ARCHIVED),
    ...                    manager_states=(PUBLISHED,),
    ...                    published_states=(PUBLISHED,),
    ...                    visible_states=(PUBLISHED,),
    ...                    waiting_states=(),
    ...                    retired_states=(),
    ...                    archived_states=(ARCHIVED,),
    ...                    auto_retired_state=(ARCHIVED,))

    >>> from pyams_utils.registry import utility_config
    >>> @utility_config(name='PyAMS basic workflow', provides=IWorkflow)
    ... class WorkflowUtility(object):
    ...     """PyAMS basic workflow utility"""
    ...
    ...     def __new__(cls):
    ...         return wf

    >>> from pyams_utils.testing import call_decorator
    >>> call_decorator(config, utility_config, WorkflowUtility,
    ...                name='PyAMS basic workflow', provides=IWorkflow)


Creating a content supporting workflow
--------------------------------------

    >>> from pyams_workflow.tests import IWfContent, IContent, WfContent, Content

    >>> wf_content = WfContent()
    >>> content = Content()
    >>> content.__parent__ = app
    >>> content.__name__ = 'content'
    >>> content.workflow_name = 'PyAMS basic workflow'

    >>> def content_workflow_adapter(context):
    ...     return getUtility(IWorkflow, name=context.workflow_name)

    >>> from pyams_workflow.interfaces import IWorkflowVersions, IWorkflowInfo
    >>> versions = IWorkflowVersions(content)
    >>> versions
    <pyams_workflow.versions.WorkflowVersions object at 0x...>

    >>> versions.add_version(wf_content, None)
    1
    >>> versions.get_version(None) is wf_content
    True
    >>> versions.get_version(1) is wf_content
    True
    >>> versions.get_version(2)
    Traceback (most recent call last):
    ...
    pyams_workflow.interfaces.VersionError: Missing given version ID 2

    >>> list(versions.get_versions())
    [<pyams_workflow.tests.WfContent object at 0x...>]

    >>> IWorkflowInfo(wf_content).fire_transition('init')

The "get_version" method, without argument, should return the last version:

    >>> versions.get_version() is wf_content
    True
    >>> list(versions.get_versions())
    [<pyams_workflow.tests.WfContent object at 0x...>]
    >>> list(versions.get_versions('draft'))
    [<pyams_workflow.tests.WfContent object at 0x...>]

    >>> list(versions.get_last_versions())
    [<pyams_workflow.tests.WfContent object at 0x...>]

Some utility functions also exists to get last versions of a given content:

    >>> from pyams_workflow.versions import get_last_version, get_last_version_in_state
    >>> get_last_version(wf_content) is wf_content
    True
    >>> get_last_version_in_state(wf_content) is wf_content
    True

    >>> from pyams_workflow.interfaces import IWorkflowVersion, IWorkflowState, IWorkflowInfo

    >>> wf_state = IWorkflowState(wf_content)
    >>> wf_state
    <pyams_workflow.versions.WorkflowVersionState object at 0x...>
    >>> wf_state.version_id
    1
    >>> wf_state.state
    'draft'
    >>> wf.get_state_label(wf_state.state)
    'Draft'

    >>> wf_info = IWorkflowInfo(wf_content)
    >>> wf_info
    <pyams_workflow.workflow.WorkflowInfo object at 0x...>

    >>> wf_info.has_automatic_transitions()
    False
    >>> wf_info.fire_automatic()
    >>> wf_state.state
    'draft'

    >>> sorted(wf_info.get_fireable_transition_ids())
    ['delete', 'draft_to_published']
    >>> wf_info.has_version(DRAFT)
    True

    >>> sorted(wf_info.get_fireable_transition_ids_toward(DELETED))
    ['delete']
    >>> sorted(wf_info.get_fireable_transition_ids_toward(ARCHIVED))
    []
    >>> sorted(wf_info.get_fireable_transition_ids_toward('unknown'))
    []

Let's try to publish our content:

    >>> wf_info.fire_transition_toward(PUBLISHED)
    >>> wf_state.state
    'published'
    >>> wf_info.fire_transition_toward('unknown')
    Traceback (most recent call last):
    ...
    pyams_workflow.interfaces.NoTransitionAvailableError: source: "published" destination: "unknown"

    >>> sorted(wf_info.get_fireable_transition_ids())
    ['published_to_archived', 'published_to_draft']

    >>> wf_state.state_date
    datetime.datetime(...)
    >>> wf_state.state_principal
    'admin:admin'

    >>> wf_state.get_first_state_date(DRAFT)
    datetime.datetime(...)

We can then check our content publication status:

    >>> publication_info = IWorkflowPublicationInfo(wf_content)
    >>> publication_info
    <pyams_workflow.content.WorkflowContentPublicationInfo object at 0x...>

    >>> publication_info.publication_date
    datetime.datetime(..., tzinfo=...)
    >>> publication_info.publication
    'on .../.../... at ...:... by ...: admin:admin'

    >>> publication_info.first_publication_date is None
    True
    >>> publication_info.content_publication_date is None
    True
    >>> publication_info.publication_effective_date is None
    True

    >>> publication_info.is_published()
    False
    >>> publication_info.is_visible(request)
    False

The document is not published, because it doesn't have any publication effective date!

    >>> from datetime import datetime
    >>> publication_info.publication_effective_date = datetime.now(timezone.utc)
    >>> publication_info.apply_first_publication_date()

    >>> publication_info.is_published()
    True
    >>> publication_info.is_visible()
    True
    >>> publication_info.displayed_publication_date
    'first'
    >>> publication_info.visible_publication_date
    datetime.datetime(..., tzinfo=...)
    >>> publication_info.push_end_date_index
    datetime.datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=<UTC>)
    >>> publication_info.content_publication_date == publication_info.first_publication_date
    True

Let's check versions history:

    >>> history = wf_state.history
    >>> len(history)
    2
    >>> history[0].source_version is None
    True

We are now going to create a new version and publish it:

    >>> sorted(wf_info.get_fireable_transition_ids_toward(DRAFT))
    ['published_to_draft']
    >>> wf_content_2 = wf_info.fire_transition_toward(DRAFT)
    >>> wf_content_2
    <pyams_workflow.tests.WfContent object at 0x...>

    >>> versions.get_version(1) is wf_content
    True
    >>> versions.get_version() is wf_content_2
    True
    >>> list(versions.get_versions())
    [<pyams_workflow.tests.WfContent object at 0x...>, <pyams_workflow.tests.WfContent object at 0x...>]
    >>> versions.last_version_id
    2

    >>> get_last_version(wf_content) is wf_content_2
    True
    >>> get_last_version_in_state(wf_content) is wf_content
    True
    >>> get_last_version_in_state(wf_content_2) is wf_content_2
    True

We can now publish the new version:

    >>> wf_info_2 = IWorkflowInfo(wf_content_2)
    >>> wf_info_2.fire_transition_toward(PUBLISHED)

The first version should now be archived:

    >>> wf_state.state
    'archived'

    >>> wf_state_2 = IWorkflowState(wf_content_2)
    >>> wf_state_2.state
    'published'

    >>> publication_info_2 = IWorkflowPublicationInfo(wf_content_2)
    >>> publication_info_2.visible_publication_date
    datetime.datetime(..., tzinfo=...)

    >>> publication_info_2.publication_effective_date = datetime.now(timezone.utc)
    >>> publication_info_2.publication_expiration_date = datetime.utcnow() + timedelta(days=10)
    >>> IWorkflowPublicationInfo.validateInvariants(publication_info_2)

    >>> publication_info_2.content_publication_date is None
    False
    >>> publication_info_2.content_publication_date == publication_info_2.first_publication_date
    False
    >>> publication_info_2.content_publication_date == publication_info.first_publication_date
    True

Let's now add another version... and remove it!

    >>> wf_content_3 = wf_info_2.fire_transition_toward(DRAFT)
    >>> wf_content_3
    <pyams_workflow.tests.WfContent object at 0x...>

    >>> versions.last_version_id
    3

    >>> wf_state_3 = IWorkflowState(wf_content_3)
    >>> wf_state_3.version_id
    3
    >>> pprint.pprint(list(versions.items()))
    [('1', <pyams_workflow.tests.WfContent object at 0x...>),
     ('2', <pyams_workflow.tests.WfContent object at 0x...>),
     ('3', <pyams_workflow.tests.WfContent object at 0x...>)]

    >>> pprint.pprint(versions.state_by_version)
    {1: 'archived', 2: 'published', 3: 'draft'}

    >>> pprint.pprint(versions.versions_by_state[DRAFT])
    [3]
    >>> pprint.pprint(versions.versions_by_state[PUBLISHED])
    [2]
    >>> pprint.pprint(versions.versions_by_state[ARCHIVED])
    [1]

    >>> versions.get_version() is wf_content_3
    True
    >>> get_last_version(wf_content) is wf_content_3
    True
    >>> get_last_version_in_state(wf_content) is wf_content
    True
    >>> get_last_version_in_state(wf_content_2) is wf_content_2
    True

    >>> wf_info_3 = IWorkflowInfo(wf_content_3)
    >>> wf_info_3.fire_transition_toward(DELETED)

Removing a version doesn't reset last version ID:

    >>> versions.last_version_id
    3

    >>> pprint.pprint(versions.deleted)
    {3: <pyams_workflow.tests.WfContent object at 0x...>}

    >>> pprint.pprint(versions.state_by_version)
    {1: 'archived', 2: 'published'}

    >>> pprint.pprint(versions.versions_by_state.get(DRAFT))
    None
    >>> pprint.pprint(versions.versions_by_state.get(PUBLISHED))
    [2]
    >>> pprint.pprint(versions.versions_by_state.get(ARCHIVED))
    [1]

Deleted versions are no more included in the list of accessible content versions:

    >>> versions.get_version() is wf_content_2
    True

Trying to archive this content directly should fail, because the transition is protected by
FORBIDDEN_PERMISSION. But this requires an active authentication policy:

    >>> from pyams_security.policy import PyAMSSecurityPolicy

    >>> policy = PyAMSSecurityPolicy(secret='PyAMS 0.1.0', http_only=True, secure=False)
    >>> config.set_security_policy(policy)

    >>> wf_info_2.fire_transition_toward(ARCHIVED)
    Traceback (most recent call last):
    ...
    pyams_workflow.interfaces.NoTransitionAvailableError: source: "published" destination: "archived"

Trying to fire the same transition manually should also fire an exception:

    >>> wf_info_2.fire_transition('published_to_archived')
    Traceback (most recent call last):
    ...
    pyramid.httpexceptions.HTTPUnauthorized: ...

A custom class implementing IWorkflowPublicationInfo can be used in specific contexts to handle
hidden contents:

    >>> from pyams_workflow.content import HiddenContentPublicationInfo
    >>> info = HiddenContentPublicationInfo()
    >>> info.is_published()
    False
    >>> info.is_visible()
    False


Workflow namespace and traverser
--------------------------------

Versions are available using a "++versions++" traverser:

    >>> from pyams_utils.url import absolute_url
    >>> absolute_url(wf_content_2, request)
    'http://example.com/content/++versions++/2'

    >>> from pyams_utils.traversing import ITraversable
    >>> traverser = request.registry.queryAdapter(content, ITraversable, name='versions')
    >>> traverser
    <pyams_workflow.versions.WorkflowVersionsTraverser object at 0x...>

    >>> traverser.traverse('') is versions
    True

    >>> traverser.traverse('2') is wf_content_2
    True


Workflow sub-locations
----------------------

Workflow versions are defined as a sub-locations adapter:

    >>> from zope.location.interfaces import ISublocations

    >>> locations = request.registry.queryAdapter(content, ISublocations, name='versions')
    >>> list(locations.sublocations())
    [<pyams_workflow.tests.WfContent object at 0x...>, <pyams_workflow.tests.WfContent object at 0x...>]


Workflow transition forms
-------------------------

PyAMS_workflow provides a base class to handle workflow transitions:

    >>> from zope.interface import alsoProvides
    >>> from pyams_layer.interfaces import IPyAMSLayer

    >>> request = DummyRequest(context=wf_content_2,
    ...                        params={'workflow.widgets.transition_id': published_to_draft.transition_id})
    >>> alsoProvides(request, IPyAMSLayer)

    >>> from pyams_workflow.zmi.transition import WorkflowContentTransitionForm

    >>> form = WorkflowContentTransitionForm(wf_content_2, request)
    >>> form.update()

    >>> form.transition is published_to_draft
    True

    >>> form.legend
    'Create new version'

Let's try to submit this form:

    >>> request = DummyRequest(context=wf_content_2,
    ...                        params={
    ...                            'workflow.widgets.transition_id': published_to_draft.transition_id,
    ...                            'workflow.buttons.add': "Add"
    ...                        })
    >>> alsoProvides(request, IPyAMSLayer)

    >>> form = WorkflowContentTransitionForm(wf_content_2, request)
    >>> form.update()

    >>> pprint.pprint(versions.state_by_version)
    {1: 'archived', 2: 'published', 4: 'draft'}


Content history view
--------------------

PyAMS provides a view to display content history:

    >>> from pyams_zmi.interfaces import IAdminLayer
    >>> from pyams_workflow.zmi.history import WorkflowVersionHistoryTable

    >>> request = DummyRequest(context=wf_content_2)
    >>> alsoProvides(request, IAdminLayer)

    >>> table = WorkflowVersionHistoryTable(wf_content_2, request)
    >>> table.update()
    >>> print(table.render())
    <table...data-ams-location='http://example.com/content/++versions++/2'...class="table table-striped table-hover table-sm datatable w-100">
      <thead >
        <tr >
          <th   data-ams-column-name='date'>Date</th>
          <th   data-ams-column-name='state'>New state</th>
          <th   data-ams-column-name='principal'>Modifier</th>
          <th   data-ams-column-name='comment'>Comment</th>
        </tr>
      </thead>
      <tbody>
        <tr  id='table_...::...'>
          <td   class="nowrap">.../.../... - ...:...</td>
          <td  >--</td>
          <td  >--</td>
          <td  >Clone created from version 1 (in « Published » state)</td>
        </tr>
        <tr  id='table_...::...'>
          <td   class="nowrap">.../.../... - ...:...</td>
          <td  >Draft</td>
          <td  >--</td>
          <td  >--</td>
        </tr>
        <tr  id='table_...::...'>
          <td   class="nowrap">.../.../... - ...:...</td>
          <td  >Published</td>
          <td  >--</td>
          <td  >--</td>
        </tr>
      </tbody>
    </table>


Content versions viewlet
------------------------

This viewlet is used to display a dropdown menu of all content versions:

    >>> from pyams_workflow.zmi.viewlet.versions import WorkflowVersionsMenu
    >>> menu = WorkflowVersionsMenu(wf_content_2, request, None, None)
    >>> menu.update()
    >>> print(menu.render())
    <div class="d-flex dropdown mx-1">
        <span class="btn btn-info btn-sm dropdown-toggle"
              data-toggle="dropdown" aria-expanded="false">
            Version 2 - Published
        </span>
        <span class="dropdown-menu">
            <a class="dropdown-item pl-3 "
               href="http://example.com/content/++versions++/4/admin#">
                <i class="fas fa-arrow-right text-secondary fa-fw mr-1"></i>
                Version 4 - Draft
            </a>
            <a class="dropdown-item pl-3 bg-primary text-white"
               href="http://example.com/content/++versions++/2/admin#">
                <i class="fas fa-arrow-right fa-fw mr-1"></i>
                Version 2 - Published
            </a>
            <a class="dropdown-item pl-3 "
               href="http://example.com/content/++versions++/1/admin#">
                <i class="fas fa-arrow-right text-secondary fa-fw mr-1"></i>
                Version 1 - Archived
            </a>
        </span>
    </div>


Content transitions viewlet
---------------------------

This viewlet is used to display a dropdown menu of all transitions which can be fired by
the current request principal:

    >>> from pyams_workflow.zmi.viewlet.transitions import WorkflowTransitionsMenu
    >>> menu = WorkflowTransitionsMenu(wf_content_2, request, None, None)
    >>> menu.update()
    >>> print(menu.render())

Why is this menu empty? That's because current workflow doesn't allow manual archives.
We can try with another version (we remove security policy to avoid setting of all
required principals and permissions):

    >>> config.set_security_policy(None)

    >>> wf_content_4 = versions.get_version(4)
    >>> wf_content_4
    <pyams_workflow.tests.WfContent object at 0x...>

    >>> menu = WorkflowTransitionsMenu(wf_content_4, request, None, None)
    >>> menu.update()
    >>> print(menu.render())
    <div class="d-flex dropdown mx-1">
        <span class="btn btn-danger btn-sm dropdown-toggle"
              data-toggle="dropdown" aria-expanded="false">
            Change status...
        </span>
        <span class="dropdown-menu">
            <a class="dropdown-item pl-3 "
               href="http://example.com/content/++versions++/4/wf-transition.html?workflow.widgets.transition_id=draft_to_published"
               data-toggle="modal"
               data-ams-modules="modal">
                <i class="fa fa-fw mr-1"></i>
                Publish
            </a>
            <div class="dropdown-divider"></div>
            <a class="dropdown-item pl-3 "
               href="http://example.com/content/++versions++/4/wf-transition.html?workflow.widgets.transition_id=delete"
               data-toggle="modal"
               data-ams-modules="modal">
                <i class="fab fa-trash fa-fw mr-1"></i>
                Delete version
            </a>
        </span>
    </div>


Tests cleanup:

    >>> tearDown()
