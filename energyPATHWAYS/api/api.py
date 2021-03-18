import subprocess
import logging
import datetime
from collections import defaultdict
from flask import Flask, g, request
from flask_restful import Resource, Api
from flask_cors import CORS
from sqlalchemy.exc import DataError
import models
import schemas

# authentication strategy based on http://blog.miguelgrinberg.com/post/restful-authentication-with-flask
# NOTE: This only provides meaningful security if the API is served exclusively over https (never http)
from flask_httpauth import HTTPBasicAuth


class NotFound(Exception):
    pass


class Forbidden(Exception):
    pass


api_errors = {
    'DataError': {
        'message': "Not Found",
        'status': 404
    },
    'NotFound': {
        'message': "Not Found",
        'status': 404
    },
    'Forbidden': {
        'message': "Forbidden",
        'status': 403
    }
}


# Initialize the application
app = Flask(__name__)
app.config.from_pyfile('config.py')

# TODO: This allows the API to respond to XMLHttpRequests from any domain. This is preferable for development, but
# for production we should restrict the allowed origin only to the Pathways web interface server
# (or just host the web app and API on the same domain, in which case there's no need for CORS)
CORS(app)
api = Api(app, errors=api_errors)
models.db.init_app(app)
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username_or_token, password):
    # if the username is guest then login is guaranteed, with the "user" being a limited "Guest" object
    if username_or_token == 'guest':
        g.user = models.Guest()
        return True
    # if the user is not a guest, first try to authenticate by token
    user = models.User.verify_auth_token(username_or_token, app.config['SECRET_KEY'])
    if not user:
        # try to authenticate with username/password
        user = models.User.query.filter_by(name=username_or_token).first()
        if not user or not user.is_correct_password(password):
            return False
    g.user = user
    return True


# Decorator that blocks guest users from performing an action. (Must come after @auth.login_required so g.user is set!)
def guest_forbidden(method):
    def restricted_method(*args, **kwargs):
        if g.user.is_guest():
            raise Forbidden
        return method(*args, **kwargs)
    return restricted_method


# Decorator indicating that the request expects an application/json content type
def expects_json(method):
    def restricted_method(*args, **kwargs):
        if not request.headers.get('Content-Type').startswith('application/json'):
            return {'status': 400, 'message': 'Your request must provide data of Content-Type: application/json'}, 400
        return method(*args, **kwargs)
    return restricted_method


# Methods to retrieve a scenario by id while respecting access controls; any time the API needs to load a scenario it
# should use one of these.
def _fetch_scenario(scenario_id):
    scenario = models.Scenario.query.get(scenario_id)
    if scenario is None:
        raise NotFound
    return scenario


def fetch_readable_scenario(scenario_id):
    scenario = _fetch_scenario(scenario_id)
    if not g.user.can_read_scenario(scenario):
        raise Forbidden
    return scenario


def fetch_owned_scenario(scenario_id):
    scenario = _fetch_scenario(scenario_id)
    if not g.user.owns_scenario(scenario):
        raise Forbidden
    return scenario


class Scenarios(Resource):
    @staticmethod
    def _location_header(scenario):
        return {'Location': api.url_for(Scenarios, scenario_id=scenario.id)}

    @classmethod
    def _duplicates(cls, list_):
        seen = set()
        dupes = []
        for item in list_:
            if item in seen:
                dupes.append(item)
            else:
                seen.add(item)
        return dupes

    @classmethod
    def _validate_scenario_data(cls, scenario_data):
        messages = defaultdict(list)
        for ds in ('demand', 'supply'):
            # set up data access specifics we'll need later on depending on whether we're currently validating the
            # demand side or the supply side
            ds_key = ds + '_package_group_ids'
            if ds == 'demand':
                case_data_class = models.DemandCaseData
                group_column = 'subsector_id'
            else:
                case_data_class = models.SupplyCaseData
                group_column = 'supply_node_id'

            request_pg_ids = scenario_data[ds_key]
            dupe_pg_ids = cls._duplicates(request_pg_ids)
            if dupe_pg_ids:
                messages[ds_key].append("Duplicated package group ids detected: %s" % (str(dupe_pg_ids),))

            found_pgs = case_data_class.query.filter(case_data_class.id.in_(request_pg_ids)).all()
            not_found_pg_ids = set(request_pg_ids) - set(pg.id for pg in found_pgs)
            if not_found_pg_ids:
                messages[ds_key].append("One or more requested package group ids were not found: %s" %
                                        (str(list(not_found_pg_ids)),))

            grouped_pgs = defaultdict(list)
            for pg in found_pgs:
                grouped_pgs[getattr(pg, group_column)].append(pg.id)
            for group_id, pg_ids in grouped_pgs.items():
                if len(pg_ids) > 1:
                    messages[ds_key].append("Too many package group ids specified for %s %i: %s" %
                                            (group_column, group_id, str(pg_ids)))

        return messages

    @auth.login_required
    def get(self, scenario_id=None):
        schema = schemas.ScenarioSchema()
        outputs_requested = 'outputs' in request.args

        if scenario_id is None:
            # If outputs are requested with the scenario list, we send only the basic outputs
            if outputs_requested:
                schema = schemas.ScenarioWithBasicOutputSchema()
            return schema.dump(g.user.readable_scenarios, many=True).data
        else:
            # If outputs are requested for an individual scenario, we send *all* the outputs
            if outputs_requested:
                schema = schemas.ScenarioWithOutputSchema()
            return schema.dump(fetch_readable_scenario(scenario_id)).data

    @auth.login_required
    @guest_forbidden
    @expects_json
    def post(self, scenario_id=None):
        if scenario_id is not None:
            return {'message': "POSTs to create a new scenario must not attempt to specify an id in the URI."}, 400

        # Note that this will only work if the request's content type is 'application/json'
        scenario_data, errors = schemas.ScenarioSchema().load(request.get_json())
        if errors:
            return {'message': 'Data for new scenario did not pass validation', 'errors': errors}, 400

        scenario_data_errors = self._validate_scenario_data(scenario_data)
        if scenario_data_errors:
            return {'message': 'Problems detected with scenario specification', 'errors': scenario_data_errors}, 400

        scenario = models.Scenario.new_with_cases(name=scenario_data['name'],
                                                  description=scenario_data['description'],
                                                  user_id=g.user.id)
        scenario.update_package_group_ids(scenario_data['demand_package_group_ids'],
                                          scenario_data['supply_package_group_ids'])

        models.db.session.add(scenario)
        models.db.session.commit()

        return {'message': 'Created', 'id': scenario.id}, 201, self._location_header(scenario)

    @auth.login_required
    @guest_forbidden
    @expects_json
    def put(self, scenario_id=None):
        if scenario_id is None:
            return {'message': "PUTs to update a scenario must specify the id in the URI."}, 400

        scenario = fetch_owned_scenario(scenario_id)
        if scenario.runs:
            return {'message': 'The requested scenario has already been run (or is currently running) and therefore '
                               'cannot be edited; consider cloning it instead.'}, 400

        scenario_data, errors = schemas.ScenarioSchema().load(request.get_json())
        if errors:
            return {'message': 'Data for updating scenario did not pass validation:', 'errors': errors}, 400

        scenario_data_errors = self._validate_scenario_data(scenario_data)
        if scenario_data_errors:
            return {'message': 'Problems detected with scenario specification', 'errors': scenario_data_errors}, 400

        scenario.name = scenario_data['name']
        scenario.description = scenario_data['description']
        scenario.update_package_group_ids(scenario_data['demand_package_group_ids'],
                                          scenario_data['supply_package_group_ids'])

        models.db.session.add(scenario)
        models.db.session.commit()

        return {'message': 'Updated'}, 200, self._location_header(scenario)

    @auth.login_required
    @guest_forbidden
    def delete(self, scenario_id=None):
        if scenario_id is None:
            return {'message': "Requests to delete a scenario must specify the id in the URI."}, 400

        scenario = fetch_owned_scenario(scenario_id)
        # We don't allow built-in scenarios to be deleted via the API (even by an admin) because it may be unsafe.
        # See comment on demand_case and supply_case relationships for Scenario in models.py for discussion.
        if scenario.is_built_in():
            return {'message': "Built-in scenarios cannot be deleted via this API."}, 400

        models.db.session.delete(scenario)
        models.db.session.commit()

        return {'message': 'Deleted'}, 200


class PackageGroups(Resource):
    # The package group options are the same for everyone, but only authorized users are allowed to make scenarios and
    # therefore only authorized users should be accessing this resource
    @auth.login_required
    def get(self):
        return {
            'subsectors': schemas.DemandSubsectorSchema().dump(
                models.DemandSubsector.query.order_by(
                    models.DemandSubsector.sector_id, models.DemandSubsector.id
                ).all(), many=True
            ).data,
            'nodes': schemas.SupplyNodeSchema().dump(
                models.SupplyNode.query.order_by(
                    models.SupplyNode.supply_type_id, models.SupplyNode.id
                ).all(), many=True
            ).data
        }


class ScenarioRunner(Resource):
    @auth.login_required
    def post(self, scenario_id):
        scenario = fetch_owned_scenario(scenario_id)
        if scenario.is_running():
            return {'message': 'Scenario is already running (or queued to run)'}, 400

        # Create a new scenario run entry for the requested scenario. The queue_monitor will later find the queued
        # scenario and actually run it.
        run = models.ScenarioRun(scenario_id=scenario.id)
        models.db.session.add(run)
        models.db.session.commit()

        return {'message': 'Scenario queued for running'}, 200,\
               {'Location': api.url_for(ScenarioRunner, scenario_id=scenario.id)}

    @auth.login_required
    def get(self, scenario_id):
        return schemas.ScenarioRunStatusSchema().dump(fetch_readable_scenario(scenario_id).status).data


class Outputs(Resource):
    @auth.login_required
    def get(self, scenario_id, output_type_id):
        scenario = fetch_readable_scenario(scenario_id)

        # We can only provide outputs for a successful run. Note that this will hide older results while waiting for
        # new ones while a Scenario is being re-run, because only the latest run is checked
        if not scenario.successfully_run():
            raise NotFound

        output = scenario.latest_run.outputs.filter(models.Output.output_type_id == output_type_id).one()
        return schemas.OutputSchema().dump(output)


class Token(Resource):
    @auth.login_required
    @guest_forbidden
    def get(self):
        token = g.user.generate_auth_token(app.config['SECRET_KEY'])
        return {'token': token.decode('ascii')}

api.add_resource(Scenarios, '/scenarios', '/scenarios/<int:scenario_id>', endpoint='scenarios')
api.add_resource(PackageGroups, '/package_groups')
api.add_resource(ScenarioRunner, '/scenarios/<int:scenario_id>/run')
api.add_resource(Outputs, '/scenarios/<int:scenario_id>/output/<int:output_type_id>')
api.add_resource(Token, '/token')

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run()

    # Logging recipe from http://flask.pocoo.org/docs/0.11/errorhandling/#logging-to-a-file
    # There's also a bunch of guidance there about sending emails on error, etc., when we're ready for that
    if not app.debug:
        logging.basicConfig(filename='../../us_model_example/api_%s.log' %
                                     datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                            level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
