import subprocess
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

    @auth.login_required
    def get(self, scenario_id=None):
        if scenario_id is None:
            return schemas.ScenarioSchema().dump(g.user.readable_scenarios, many=True).data
        else:
            return schemas.ScenarioSchema().dump(fetch_readable_scenario(scenario_id)).data

    @auth.login_required
    @guest_forbidden
    @expects_json
    def post(self, scenario_id=None):
        if scenario_id is not None:
            return {'message': "POSTs to create a new scenario must not attempt to specify an id in the URI."}, 400

        # Note that this will only work if the request's content type is 'application/json'
        scenario_data, errors = schemas.ScenarioSchema().load(request.get_json())
        if errors:
            return {'message': 'Data for new scenario did not pass validation:', 'errors': errors}, 400

        # TODO: possible worthwhile things to validate (these go for the put() below as well)
        # 1. that all of the demand package groups and supply package groups requested actually exist
        # (at the moment any that don't exist will simply be ignored because nothing in the database will match
        # them in the in_() calls below)
        # 2. that the user did not try to select more than one package group for the same subsector / node
        scenario = models.Scenario.new_with_cases(name=scenario_data['name'],
                                                  description=scenario_data['description'],
                                                  user_id=g.user.id)
        scenario.update_package_group_ids(scenario_data['demand_package_group_ids'],
                                          scenario_data['supply_package_group_ids'])

        models.db.session.add(scenario)
        models.db.session.commit()

        return {'message': 'Created'}, 201, self._location_header(scenario)

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

        scenario.name = scenario_data['name']
        scenario.description = scenario_data['description']
        scenario.update_package_group_ids(scenario_data['demand_package_group_ids'],
                                          scenario_data['supply_package_group_ids'])

        models.db.session.add(scenario)
        models.db.session.commit()

        return {'message': 'Updated'}, 200, self._location_header(scenario)


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
        run = models.ScenarioRun(scenario_id=scenario.id)
        models.db.session.add(run)
        models.db.session.commit()

        # Actually run the scenario
        subprocess.Popen(['energyPATHWAYS', '-a',
                          '-p', '../../us_model_example',
                          '-s', str(scenario_id)])

        return {'message': 'Scenario run initiated'}, 200,\
               {'Location': api.url_for(ScenarioRunner, scenario_id=scenario.id)}

    @auth.login_required
    def get(self, scenario_id):
        return schemas.ScenarioRunStatusSchema().dump(fetch_owned_scenario(scenario_id).status).data


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
    app.config.from_pyfile('config.py')
    app.run(debug=True)
