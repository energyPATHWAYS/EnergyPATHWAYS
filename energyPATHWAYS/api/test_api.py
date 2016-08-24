import unittest
import mock
import json
import api
import base64
import sqlalchemy.schema as schema
from sqlalchemy.sql.expression import func
import models


class TestAPI(unittest.TestCase):
    SCENARIOS_PATH = '/scenarios'

    def setUp(self):
        api.app.config.from_pyfile('test_config.py')
        api.app.testing = True
        self.test_app = api.app.test_client()

        with api.app.app_context():
            # create tables
            models.db.engine.execute(schema.DDL('CREATE SCHEMA IF NOT EXISTS ' + models.GLOBAL_SCHEMA))
            models.db.engine.execute(schema.DDL('CREATE SCHEMA IF NOT EXISTS ' + models.RUN_SCHEMA))
            models.db.create_all()

            # users for testing
            self.admin_credentials = {'name': 'admin', 'password': 'terrible'}
            admin = models.User(email='admin@example.com', admin=True, **self.admin_credentials)
            self.jane_doe_credentials = {'name': 'Jane', 'password': 'rainbow'}
            jane_doe = models.User(email='jane_doe@example.com', admin=False, **self.jane_doe_credentials)
            models.db.session.add_all([admin, jane_doe])

            # demand sectors
            models.db.session.add_all([
                models.DemandSector(id=1, name='residential'),
                models.DemandSector(id=2, name='commercial'),
                models.DemandSector(id=3, name='transportation'),
                models.DemandSector(id=4, name='productive')
            ])

            # demand subsectors for testing
            light_duty_vehicles = models.DemandSubsector(name='Light Duty Vehicles', sector_id=3)
            for i in range(3):
                light_duty_vehicles.demand_case_data.append(models.DemandCaseData(description='LDV option ' + str(i)))
            commercial_lighting = models.DemandSubsector(name='Commercial Lighting', sector_id=2)
            for i in range(2):
                commercial_lighting.demand_case_data.append(models.DemandCaseData(description='CL option ' + str(i)))
            residential_heating = models.DemandSubsector(name='Residential Heating', sector_id=1)
            residential_heating.demand_case_data.append(models.DemandCaseData(description='RH only option'))
            models.db.session.add_all([light_duty_vehicles, commercial_lighting, residential_heating])

            # supply types
            models.db.session.add_all([
                models.SupplyType(id=1, name='Blend'),
                models.SupplyType(id=2, name='Conversion'),
                models.SupplyType(id=3, name='Delivery'),
                models.SupplyType(id=4, name='Import'),
                models.SupplyType(id=5, name='Primary'),
                models.SupplyType(id=6, name='Storage')
            ])

            # supply nodes for testing
            rooftop_pv = models.SupplyNode(name='Rooftop Solar PV', supply_type_id=2)
            for _ in range(3):
                rooftop_pv.supply_case_data.append(models.SupplyCaseData())
            gasoline_blend = models.SupplyNode(name='Gasoline Blend', supply_type_id=1)
            for _ in range(2):
                gasoline_blend.supply_case_data.append(models.SupplyCaseData())
            uranium = models.SupplyNode(name='Uranium Import', supply_type_id=4)
            uranium.supply_case_data.append(models.SupplyCaseData())
            models.db.session.add_all([rooftop_pv, gasoline_blend, uranium])

            # scenarios for testing
            # a built-in scenario
            builtin = models.Scenario.new_with_cases(name='Test Built-In Scenario',
                                                     description='Built-in and built tough')
            builtin.demand_case.data.append(light_duty_vehicles.demand_case_data[0])
            builtin.demand_case.data.append(commercial_lighting.demand_case_data[1])
            builtin.supply_case.data.append(rooftop_pv.supply_case_data[0])
            # an admin-created scenario
            admin_scenario = models.Scenario.new_with_cases(name='Test Admin-Created Scenario',
                                                            description='Administratively affirmed',
                                                            user=admin)
            admin_scenario.demand_case.data.append(light_duty_vehicles.demand_case_data[1])
            # a user-created scenario
            jane_scenario = models.Scenario.new_with_cases(name='Test User-Created Scenario',
                                                           description='Plain Jane',
                                                           user=jane_doe)
            jane_scenario.demand_case.data.append(light_duty_vehicles.demand_case_data[2])
            models.db.session.add_all([builtin, admin_scenario, jane_scenario])

            # populate the scenario_run_statuses and output_types tables
            models.db.session.add_all(models.ScenarioRunStatus.contents())
            models.db.session.add_all(models.OutputType.contents())

            models.db.session.commit()

            self.bultin_scenario_id = builtin.id
            self.admin_scenario_id = admin_scenario.id
            self.jane_scenario_id = jane_scenario.id

    def tearDown(self):
        with api.app.app_context():
            models.db.drop_all()

    # Add an HTTP Authorization header for the requested User to the provided request kwargs.
    # credentials is expected to be dict-like and provide 'name' and 'password'.
    # If no user is provided, assume guest access.
    def _add_auth_header(self, credentials, **kwargs):
        if credentials is None:
            name = 'guest'
            password = ''
        else:
            name = credentials['name']
            password = credentials['password']

        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = 'Basic ' + base64.b64encode(name + ':' + password)
        return kwargs

    def get(self, path, credentials=None, **kwargs):
        return self.test_app.get(path, **self._add_auth_header(credentials, **kwargs))

    def post(self, path, credentials=None, **kwargs):
        return self.test_app.post(path, **self._add_auth_header(credentials, **kwargs))

    def put(self, path, credentials=None, **kwargs):
        return self.test_app.put(path, **self._add_auth_header(credentials, **kwargs))

    # Get the list of package groups that we can choose from
    def load_options(self, credentials):
        rv = self.get('/package_groups', credentials)
        self.assertEqual(rv.status_code, 200)
        return json.loads(rv.data)

    @mock.patch('subprocess.Popen')
    def run_scenario(self, scenario_id, credentials, mock_popen):
        """
        Posts to the scenario run route but with the subprocess starter mocked so we don't actually get
        models running while running unit tests. Always use this when kicking off scenario runs within a unit test!
        """
        rv = self.post('/scenarios/%i/run' % (scenario_id,), credentials)
        # If a success status was returned, we expect that a model run subprocess was started
        # Conversely, if any other code was returned, we expect that a model run subprocess was *not* started!
        self.assertEqual(rv.status_code == 200, mock_popen.called)
        return rv

    def test_package_groups(self):
        options = self.load_options(self.jane_doe_credentials)

        # Supply nodes are sorted by supply_type_id
        self.assertEqual(options['nodes'][0]['supply_type_id'], 1)
        self.assertEqual(options['nodes'][0]['supply_type_name'], 'Blend')
        self.assertEqual(options['nodes'][-1]['supply_type_id'], 4)
        self.assertEqual(options['nodes'][-1]['supply_type_name'], 'Import')

        # Demand subsectors are sorted by sector
        self.assertEqual(options['subsectors'][0]['sector_id'], 1)
        self.assertEqual(options['subsectors'][0]['sector_name'], 'residential')
        self.assertEqual(options['subsectors'][-1]['sector_id'], 3)
        self.assertEqual(options['subsectors'][-1]['sector_name'], 'transportation')

    def test_scenario_list(self):
        # Unauthorized users cannot access the /scenarios route.
        # Note that unlike all the other tests, we use the raw test_app.get() here instead of the test class' get()
        # method so that we can make a request without having a guest authorization header added automatically.
        rv = self.test_app.get(self.SCENARIOS_PATH)
        self.assertEqual(rv.status_code, 401)

        # Guest can see one scenario, the built-in one
        rv = self.get(self.SCENARIOS_PATH)
        self.assertEqual(rv.status_code, 200)
        resp = json.loads(rv.data)
        self.assertEqual(len(resp), 1)
        self.assertTrue(resp[0]['is_built_in'])

        # Jane can see two scenarios; the built-in one and her own (not the admin-created one)
        rv = self.get(self.SCENARIOS_PATH, self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        resp = json.loads(rv.data)
        self.assertEqual(len(resp), 2)

        # Admin can see all three scenarios
        rv = self.get(self.SCENARIOS_PATH, self.admin_credentials)
        self.assertEqual(rv.status_code, 200)
        resp = json.loads(rv.data)
        self.assertEqual(len(resp), 3)

    def test_scenario_detail(self):
        # Jane can get her scenario and the built-in scenario, but not the admin's scenario
        rv = self.get('%s/%i' % (self.SCENARIOS_PATH, self.jane_scenario_id), self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        rv = self.get('%s/%i' % (self.SCENARIOS_PATH, self.bultin_scenario_id), self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        with self.assertRaises(api.Forbidden):
            self.get('%s/%i' % (self.SCENARIOS_PATH, self.admin_scenario_id), self.jane_doe_credentials)

        # Trying to get an id that doesn't exist results in a 404 Not Found
        with api.app.app_context():
            max_id = models.db.session.query(func.max(models.Scenario.id)).scalar()
        with self.assertRaises(api.NotFound):
            self.get('%s/%i' % (self.SCENARIOS_PATH, max_id + 1), self.jane_doe_credentials)

    def test_create_scenario(self):
        options = self.load_options(self.jane_doe_credentials)

        # Set up a dict describing the scenario we'd like to create
        scenario_name = "Jane's new scenario"
        scenario_description = "This scenario explores excellence through synergy"
        scenario_data = json.dumps(
            dict(name=scenario_name,
                 description=scenario_description,
                 demand_package_group_ids=[options['subsectors'][0]['demand_case_data'][0]['id']],
                 supply_package_group_ids=[options['nodes'][0]['supply_case_data'][0]['id']]
                 )
        )

        # An otherwise valid post will be rejected (Bad Request) if it doesn't have the application/json Content-Type
        rv = self.post(self.SCENARIOS_PATH, self.jane_doe_credentials,
                       data=scenario_data)
        self.assertEqual(rv.status_code, 400)

        # Post the new scenario correctly
        rv = self.post(self.SCENARIOS_PATH, self.jane_doe_credentials,
                       headers={'Content-Type': 'application/json'},
                       data=scenario_data)
        self.assertEqual(rv.status_code, 201)
        response_data = json.loads(rv.data)
        self.assertEqual(response_data['message'], 'Created')
        self.assertIsInstance(response_data['id'], int)

        # The Location header returned from the post takes us to the detail for the new scenario, where we can
        # confirm that the details are correct
        rv = self.get(rv.headers['Location'], self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        scenario = json.loads(rv.data)
        self.assertEqual(scenario['name'], scenario_name)
        self.assertEqual(scenario['description'], scenario_description)
        self.assertFalse(scenario['is_built_in'])
        self.assertEqual(len(scenario['demand_package_group_ids']), 1)
        self.assertEqual(len(scenario['supply_package_group_ids']), 1)
        with api.app.app_context():
            username = models.Scenario.query.get(scenario['id']).user.name
        self.assertEqual(username, self.jane_doe_credentials['name'])

        # verify that a guest can't create the same scenario
        with self.assertRaises(api.Forbidden):
            self.post(self.SCENARIOS_PATH, headers={'Content-Type': 'application/json'}, data=scenario_data)

    def test_update_scenario(self):
        modified_marker = ' modified!'
        options = self.load_options(self.jane_doe_credentials)

        # Find Jane's existing scenario (which will be the one she can see that isn't built-in)
        rv = self.get(self.SCENARIOS_PATH, self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        scenario = [s for s in json.loads(rv.data) if not s['is_built_in']][0]

        # Make sure the scenario contents are as we expect
        self.assertEqual(len(scenario['demand_package_group_ids']), 1)
        self.assertEqual(len(scenario['supply_package_group_ids']), 0)

        # Prepare a modified scenario (with a supply_package_group_id) and PUT it
        scenario_data = json.dumps(
            dict(name=scenario['name'] + modified_marker,
                 description=scenario['description'] + modified_marker,
                 demand_package_group_ids=scenario['demand_package_group_ids'],
                 supply_package_group_ids=scenario['supply_package_group_ids'] +
                                          [options['nodes'][0]['supply_case_data'][0]['id']]
                 )
        )
        rv = self.put('%s/%i' % (self.SCENARIOS_PATH, scenario['id']), self.jane_doe_credentials,
                      headers={'Content-Type': 'application/json'},
                      data=scenario_data)
        self.assertEqual(rv.status_code, 200)

        # Check that the scenario has been modified as expected
        rv = self.get(rv.headers['Location'], self.jane_doe_credentials)
        modified_scenario = json.loads(rv.data)
        self.assertEqual(modified_scenario['name'], scenario['name'] + modified_marker)
        self.assertEqual(modified_scenario['description'], scenario['description'] + modified_marker)
        # Still one demand package group like before
        self.assertEqual(len(modified_scenario['demand_package_group_ids']), 1)
        # But now also with the supply package group we added
        self.assertEqual(len(modified_scenario['supply_package_group_ids']), 1)

        # Initiate a run of the scenario
        rv = self.run_scenario(self.jane_scenario_id, self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)

        # The scenario cannot be edited now that it is running
        rv = self.put('%s/%i' % (self.SCENARIOS_PATH, scenario['id']), self.jane_doe_credentials,
                      headers={'Content-Type': 'application/json'},
                      data=scenario_data)
        self.assertEqual(rv.status_code, 400)

    def test_run_scenario(self):
        # Check the response to a status check when the scenario has never been run before
        rv = self.get('/scenarios/%i/run' % (self.jane_scenario_id,), self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(rv.data)['name'], 'Never run')

        # Initiate a new run of the scenario
        rv = self.run_scenario(self.jane_scenario_id, self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)

        # The Scenario is now queued
        rv = self.get(rv.headers['Location'], self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(rv.data)['name'], 'Queued')

        # An attempt to run the same scenario again after it's queued is rejected
        rv = self.run_scenario(self.jane_scenario_id, self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 400)

    def test_outputs(self):
        output_type_id = 3
        outputs_path = '/scenarios/%i/output/%i' % (self.jane_scenario_id, output_type_id)

        # Can't get outputs for a scenario that's never been run
        with self.assertRaises(api.NotFound):
            self.get(outputs_path, self.jane_doe_credentials)

        # Start a run for the scenario
        rv = self.run_scenario(self.jane_scenario_id, self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)

        # Still can't get outputs because the run has not successfully completed
        with self.assertRaises(api.NotFound):
            self.get(outputs_path, self.jane_doe_credentials)

        # Add some fake outputs and push the run through to successful completion
        scenario_id = self.jane_scenario_id
        unit = 'moonbeams'
        with api.app.app_context():
            run = models.Scenario.query.get(scenario_id).latest_run
            run.status_id = models.ScenarioRunStatus.SUCCESS_ID
            run.outputs.append(models.Output(
                output_type_id=output_type_id,
                unit=unit,
                data=[
                    models.OutputData(series='pony', year='2015', value='1.5'),
                    models.OutputData(series='pony', year='2025', value='2.5'),
                    models.OutputData(series='pony', year='2035', value='3.5'),
                    models.OutputData(series='bear', year='2030', value='10'),
                    models.OutputData(series='bear', year='2025', value='20'),
                    models.OutputData(series='bear', year='2020', value='5'),
                ]
            ))
            models.db.session.add(run)
            models.db.session.commit()

        # Now we can retrieve the output data
        rv = self.get(outputs_path, self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        resp = json.loads(rv.data)
        self.assertEqual(resp['output_type_id'], output_type_id)
        self.assertEqual(resp['output_type_name'], 'Energy demand')
        self.assertEqual(resp['unit'], unit)
        self.assertEqual(len(resp['data']), 6)
        # Data should come back sorted, so we'll test some specific expectations for the first row
        first_point = resp['data'][0]
        self.assertEqual(first_point['series'], 'bear')
        self.assertEqual(first_point['year'], 2020)


    def test_token(self):
        # Acquire an authentication token for Jane
        rv = self.get('/token', self.jane_doe_credentials)
        self.assertEqual(rv.status_code, 200)
        token_credentials = dict(name=json.loads(rv.data)['token'], password='')

        # Check that the view of Scenarios accessed with the token is the same as if we access with Jane's
        # username and password
        token_rv = self.get(self.SCENARIOS_PATH, token_credentials)
        self.assertEqual(token_rv.status_code, 200)
        self.assertEqual(len(json.loads(token_rv.data)), 2)
        user_rv = self.get(self.SCENARIOS_PATH, self.jane_doe_credentials)
        self.assertEqual(token_rv.data, user_rv.data)


if __name__ == "__main__":
    unittest.main()
