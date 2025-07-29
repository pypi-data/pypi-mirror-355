"""
Creates a test case class for use with the unittest library that is build into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.service.testcase.dockermongo import MockDockerMongoManager
from heaserver.settings import service
from heaobject.user import TEST_USER, NONE_USER
from heaobject.registry import Collection
from heaobject.keychain import Credentials
from heaobject.person import Person, Role, Group
from heaobject.settings import SettingsObject
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_SETTINGS_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'instance_id': f'{SettingsObject.get_type_name()}^666f6f2d6261722d71757578',
        'display_name': 'Credentials',
        'invites': [],
        'name': 'heasettings|credentials',
        'owner': NONE_USER,
        'type': 'heaobject.settings.SettingsObject',
        'user': TEST_USER,
        'shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'user': TEST_USER,
            'permissions': [Permission.VIEWER.name],
            'type_display_name': 'Settings Object'
        }],
        'actual_object_type_name': Collection.get_type_name(),
        'actual_object_uri': f'collections/{Credentials.get_type_name()}',
        'actual_object_id': Credentials.get_type_name(),
        'created': None,
        'modified': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'mime_type': 'application/x.settingsobject',
        'source': None,
        'source_detail': None,
        'type_display_name': 'Settings Object',
        'shares': []
    },
    {
        'id': '0123456789ab0123456789ab',
        'instance_id': f'{SettingsObject.get_type_name()}^0123456789ab0123456789ab',
        'display_name': 'Profile',
        'invites': [],
        'modified': None,
        'name': 'heasettings|profile',
        'owner': NONE_USER,
        'type': 'heaobject.settings.SettingsObject',
        'user': TEST_USER,
        'shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'user': TEST_USER,
            'permissions': [Permission.VIEWER.name],
            'type_display_name': 'Settings Object'
        }],
        'actual_object_type_name': Person.get_type_name(),
        'actual_object_uri': 'people/me',
        'actual_object_id': 'me',
        'created': None,
        'modified': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'mime_type': 'application/x.settingsobject',
        'source': None,
        'source_detail': None,
        'type_display_name': 'Settings Object',
        'shares': []
    },
        {
            'id': '0123456789ab0123456789ac',
            'instance_id': f'{SettingsObject.get_type_name()}^0123456789ab0123456789ac',
            'display_name': 'People',
            'invites': [],
            'modified': None,
            'name': 'heasettings|people',
            'owner': NONE_USER,
            'type': 'heaobject.settings.SettingsObject',
            'user': TEST_USER,
            'shares': [{
                'invite': None,
                'type': 'heaobject.root.ShareImpl',
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name],
                'type_display_name': 'Settings Object'
            }],
            'actual_object_type_name': Person.get_type_name(),
            'actual_object_uri': 'collections/' + Person.get_type_name(),
            'actual_object_id': Person.get_type_name(),
            'created': None,
            'modified': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'mime_type': 'application/x.settingsobject',
            'source': None,
            'source_detail': None,
            'type_display_name': 'Settings Object',
            'shares': []
        },
        {
            'id': '0123456789ab0123456789ad',
            'instance_id': f'{SettingsObject.get_type_name()}^0123456789ab0123456789ad',
            'display_name': 'Roles',
            'invites': [],
            'modified': None,
            'name': 'heasettings|roles',
            'owner': NONE_USER,
            'type': 'heaobject.settings.SettingsObject',
            'user': TEST_USER,
            'shares': [{
                'invite': None,
                'type': 'heaobject.root.ShareImpl',
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name],
                'type_display_name': 'Settings Object'
            }],
            'actual_object_type_name': Role.get_type_name(),
            'actual_object_uri': 'collections/' + Role.get_type_name(),
            'actual_object_id': Role.get_type_name(),
            'created': None,
            'modified': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'mime_type': 'application/x.settingsobject',
            'source': None,
            'source_detail': None,
            'type_display_name': 'Settings Object',
            'shares': []
        },
        {
            'id': '0123456789ab0123456789ae',
            'instance_id': f'{SettingsObject.get_type_name()}^0123456789ab0123456789ae',
            'display_name': 'Groups',
            'invites': [],
            'modified': None,
            'name': 'heasettings|groups',
            'owner': NONE_USER,
            'type': 'heaobject.settings.SettingsObject',
            'user': TEST_USER,
            'shares': [{
                'invite': None,
                'type': 'heaobject.root.ShareImpl',
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name],
                'type_display_name': 'Settings Object'
            }],
            'actual_object_type_name': Group.get_type_name(),
            'actual_object_uri': 'collections/' + Group.get_type_name(),
            'actual_object_id': Group.get_type_name(),
            'created': None,
            'modified': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'mime_type': 'application/x.settingsobject',
            'source': None,
            'source_detail': None,
            'type_display_name': 'Settings Object',
            'shares': []
        },
        {
            'id': '0123456789ab0123456789af',
            'instance_id': f'{SettingsObject.get_type_name()}^0123456789ab0123456789af',
            'display_name': 'Collections',
            'invites': [],
            'modified': None,
            'name': 'heasettings|collections',
            'owner': NONE_USER,
            'type': 'heaobject.settings.SettingsObject',
            'user': TEST_USER,
            'shares': [{
                'invite': None,
                'type': 'heaobject.root.ShareImpl',
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name],
                'type_display_name': 'Settings Object'
            }],
            'actual_object_type_name': Collection.get_type_name(),
            'actual_object_uri': 'collections/' + Collection.get_type_name(),
            'actual_object_id': Collection.get_type_name(),
            'created': None,
            'modified': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'mime_type': 'application/x.settingsobject',
            'source': None,
            'source_detail': None,
            'type_display_name': 'Settings Object',
            'shares': []
        }
    ]}

SettingsObjectTestCase = get_test_case_cls_default(coll=service.MONGODB_SETTINGS_COLLECTION,
                                              href='http://localhost:8080/settings/',
                                              wstl_package=service.__package__,
                                              db_manager_cls=MockDockerMongoManager,
                                              fixtures=db_store,
                                              get_actions=[
                                                  Action(name='heaserver-settings-settings-object-get-properties',
                                                         rel=['hea-properties']),
                                                  Action(name='heaserver-settings-settings-object-get-open-choices',
                                                         rel=['hea-opener-choices'],
                                                         url='http://localhost:8080/settings/{id}/opener'),
                                                  Action(name='heaserver-settings-settings-object-get-self',
                                                         rel=['self'],
                                                         url='http://localhost:8080/settings/{id}'),
                                                  Action(name='heaserver-settings-settings-object-get-actual',
                                                         rel=['hea-actual'],
                                                         url='http://localhost:8080/{+actual_object_uri}')],
                                              get_all_actions=[
                                                  Action(name='heaserver-settings-settings-object-get-properties',
                                                         rel=['hea-properties']),
                                                  Action(name='heaserver-settings-settings-object-get-open-choices',
                                                         rel=['hea-opener-choices'],
                                                         url='http://localhost:8080/settings/{id}/opener'),
                                                  Action(name='heaserver-settings-settings-object-get-self',
                                                         rel=['self'],
                                                         url='http://localhost:8080/settings/{id}'),
                                                  Action(name='heaserver-settings-settings-object-get-actual',
                                                         rel=['hea-actual'],
                                                         url='http://localhost:8080/{+actual_object_uri}')])

