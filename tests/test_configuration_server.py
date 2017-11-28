import json

from flask import current_app

import core.config.config
import core.config.paths
from server.returncodes import *
from tests.util.servertestcase import ServerTestCase


class TestConfigurationServer(ServerTestCase):
    def setUp(self):
        config_fields = [x for x in dir(core.config.config) if
                         not x.startswith('__') and type(getattr(core.config.config, x)).__name__
                         in ['str', 'unicode']]
        path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__')
                                                             and type(getattr(core.config.paths, x)).__name__
                                                             in ['str', 'unicode'])]
        self.original_configs = {key: getattr(core.config.config, key) for key in config_fields}
        self.original_paths = {key: getattr(core.config.paths, key) for key in path_fields}
        try:
            with open(core.config.paths.config_path) as config_file:
                self.original_config_file = config_file.read()
        except:
            self.original_config_file = '{}'

    def preTearDown(self):
        for key, value in self.original_paths.items():
            setattr(core.config.paths, key, value)

    def tearDown(self):
        for key, value in self.original_configs.items():
            setattr(core.config.config, key, value)
        with open(core.config.paths.config_path, 'w') as config_file:
            config_file.write(self.original_config_file)

    def test_get_configuration(self):
        expected = {'workflows_path': core.config.paths.workflows_path,
                    'db_path': core.config.paths.db_path,
                    'case_db_path': core.config.paths.case_db_path,
                    'log_config_path': core.config.paths.logging_config_path,
                    'host': core.config.config.host,
                    'port': int(core.config.config.port),
                    'walkoff_db_type': core.config.config.walkoff_db_type,
                    'case_db_type': core.config.config.case_db_type,
                    'clear_case_db_on_startup': bool(core.config.config.reinitialize_case_db_on_startup),
                    'number_processes': int(core.config.config.num_processes),
                    'access_token_duration': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds / 60),
                    'refresh_token_duration': int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days)}
        response = self.get_with_status_check('/api/configuration', headers=self.headers)
        self.assertDictEqual(response, expected)

    def test_set_configuration(self):
        data = {"workflows_path": 'workflows_path_reset',
                "db_path": 'db_path_reset',
                "host": 'host_reset',
                "port": 1100,
                "access_token_duration": 20,
                "refresh_token_duration": 35}
        self.post_with_status_check('/api/configuration', headers=self.headers, data=json.dumps(data),
                                    content_type='application/json')

        expected = {core.config.paths.workflows_path: 'workflows_path_reset',
                    core.config.paths.db_path: 'db_path_reset',
                    core.config.config.host: 'host_reset',
                    core.config.config.port: 1100}

        for actual, expected_ in expected.items():
            self.assertEqual(actual, expected_)

        self.assertEqual(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds, 20 * 60)
        self.assertEqual(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days, 35)

    def test_set_configuration_invalid_token_durations(self):
        access_token_duration = current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds
        refresh_token_duration = current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days
        data = {"access_token_duration": 60 * 25,
                "refresh_token_duration": 1}
        self.post_with_status_check('/api/configuration', headers=self.headers, data=json.dumps(data),
                                    content_type='application/json', status_code=BAD_REQUEST)

        self.assertEqual(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds, access_token_duration)
        self.assertEqual(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days, refresh_token_duration)
