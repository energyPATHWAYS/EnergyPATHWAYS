from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import func
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)


db = SQLAlchemy()
bcrypt = Bcrypt()

# This is the schema that stores information that is global to all models. As of this writing, that is just users.
GLOBAL_SCHEMA = 'shared'
# The idea here is that there would be a separate 'runs' schema for each model that stores all of the transient
# information about runs (including outputs). This schema is kept separate from the core model schema so that
# the model itself can easily be dumped and restored without dragging all the outputs along. Of course, if
# a Scenario is deleted in the main model during a restore this could cause referential integrity problems
# in the run schema.
RUN_SCHEMA = 'public_runs'


class DemandSector(db.Model):
    __tablename__ = 'DemandSectors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    # more columns I'm ignoring for now...


class SupplyType(db.Model):
    __tablename__ = 'SupplyTypes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)


class DemandSubsector(db.Model):
    __tablename__ = 'DemandSubsectors'
    id = db.Column(db.Integer, primary_key=True)
    sector_id = db.Column(db.ForeignKey(DemandSector.id))
    name = db.Column(db.Text)
    # more columns I'm ignoring for now...

    sector = db.relationship(DemandSector)

    def sector_name(self):
        return self.sector.name


class SupplyNode(db.Model):
    __tablename__ = 'SupplyNodes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    supply_type_id = db.Column(db.ForeignKey(SupplyType.id))
    # more columns I'm ignoring for now...

    supply_type = db.relationship(SupplyType)

    def supply_type_name(self):
        return self.supply_type.name


class DemandCaseData(db.Model):
    __tablename__ = 'DemandCasesData'
    id = db.Column(db.Integer, primary_key=True)
    subsector_id = db.Column(db.ForeignKey(DemandSubsector.id))
    description = db.Column(db.Text)
    # more columns I'm ignoring for now...

    subsector = db.relationship(DemandSubsector, backref='demand_case_data')


class SupplyCaseData(db.Model):
    __tablename__ = 'SupplyCasesData'
    id = db.Column(db.Integer, primary_key=True)
    supply_node_id = db.Column(db.ForeignKey(SupplyNode.id))
    description = db.Column(db.Text)
    # more columns I'm ignoring for now...

    node = db.relationship(SupplyNode, backref='supply_case_data')


class DemandCase(db.Model):
    __tablename__ = 'DemandCases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)

    data = db.relationship(DemandCaseData, secondary=lambda: demand_case_demand_case_data, backref='demand_cases')


class SupplyCase(db.Model):
    __tablename__ = 'SupplyCases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)

    data = db.relationship(SupplyCaseData, secondary=lambda: supply_case_supply_case_data, backref='supply_cases')


# Join table for many-to-many relationship
demand_case_demand_case_data = db.Table(
    'DemandCasesDemandCasesData',
    db.Model.metadata,
    db.Column('demand_case_id', db.ForeignKey(DemandCase.id)),
    db.Column('demand_case_data_id', db.ForeignKey(DemandCaseData.id)),
    db.PrimaryKeyConstraint('demand_case_id', 'demand_case_data_id')
)

# Join table for many-to-many relationship
supply_case_supply_case_data = db.Table(
    'SupplyCasesSupplyCasesData',
    db.Model.metadata,
    db.Column('supply_case_id', db.ForeignKey(SupplyCase.id)),
    db.Column('supply_case_data_id', db.ForeignKey(SupplyCaseData.id)),
    db.PrimaryKeyConstraint('supply_case_id', 'supply_case_data_id')
)


class Scenario(db.Model):
    __tablename__ = 'Scenarios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    description = db.Column(db.Text)
    # note the extra table column name here since in the database the columns storing these ids don't end with '_id'
    demand_case_id = db.Column('demand_case', db.ForeignKey(DemandCase.id))
    supply_case_id = db.Column('supply_case', db.ForeignKey(SupplyCase.id))
    user_id = db.Column(db.ForeignKey(GLOBAL_SCHEMA + '.users.id'))

    demand_case = db.relationship(DemandCase)
    supply_case = db.relationship(SupplyCase)

    # Note that this relies on the runs backref being sorted with most recent first
    @property
    def latest_run(self):
        return self.runs[0] if self.runs else None

    @property
    def status(self):
        if self.latest_run is None:
            # This is a bit of a hack arising from the fact that we want the scenario to have a status even
            # when it has no runs, so we fabricate a fake one. I think it's acceptable but it has a bit of code
            # smell and could probably use revisiting.
            return ScenarioRunStatus(id=ScenarioRunStatus.NEVER_RUN_ID, name='Never run',
                                     description='This scenario has never been run', finished=False)
        else:
            return self.latest_run.status

    # This makes the assumption that a Scenario will have at most one active run at a time, and if it has an active
    # run it will be the most recent run. The API enforces this, but it is possible to manually muck it up in the
    # database.
    def is_running(self):
        return self.latest_run and not self.latest_run.status.finished

    def successfully_run(self):
        return self.latest_run and self.latest_run.status.successful

    def demand_package_group_ids(self):
        return [dcd.id for dcd in self.demand_case.data]

    def supply_package_group_ids(self):
        return [scd.id for scd in self.supply_case.data]

    # Updates the Scenario's Cases' associated DemandCaseData and SupplyCaseData ids to the arrays of integers
    # passed in. Note that this will discard any previously associated DemandCaseData and SupplyCaseData.
    def update_package_group_ids(self, new_demand_package_group_ids, new_supply_package_group_ids):
        self.demand_case.data = DemandCaseData.query.filter(DemandCaseData.id.in_(new_demand_package_group_ids)).all()
        self.supply_case.data = SupplyCaseData.query.filter(SupplyCaseData.id.in_(new_supply_package_group_ids)).all()

    def is_built_in(self):
        # built-in scenarios (which are readable by everybody) have a NULL/None user_id
        return self.user_id is None

    @classmethod
    def built_ins(cls):
        return cls.query.filter_by(user_id=None).all()

    # a helper method to automatically attach an empty DemandCase and SupplyCase to a new scenario
    @classmethod
    def new_with_cases(cls, **kwargs):
        scenario = cls(**kwargs)
        scenario.demand_case = DemandCase(name=scenario.name)
        scenario.supply_case = SupplyCase(name=scenario.name)
        return scenario


# Note: ideally, this and other "system" (universal) tables could be put in the 'shared' schema, but I don't want
# to undertake to move the rest of the system tables right now so I am leaving this in the model run schema
# for consistency.
class ScenarioRunStatus(db.Model):
    __tablename__ = 'scenario_run_statuses'
    __table_args__ = {'schema': RUN_SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False, unique=True)
    finished = db.Column(db.Boolean, nullable=False)

    NEVER_RUN_ID = 0
    QUEUED_ID = 1
    RUNNING_ID = 2
    SUCCESS_ID = 3
    ERROR_ID = 4
    CANCELED_ID = 5

    @property
    def successful(self):
        return self.id == self.SUCCESS_ID

    # This provides a consistent way to set up the contents of the table whether migrating an existing database
    # or setting up a test database. Just do `session.add_all(ScenarioRunStatus.contents())` then commit the session.
    @classmethod
    def contents(cls):
        return [
            cls(id=cls.QUEUED_ID, name='Queued', description='Scenario is awaiting its turn to run', finished=False),
            cls(id=cls.RUNNING_ID, name='Running', description='Scenario is currently running', finished=False),
            cls(id=cls.SUCCESS_ID, name='Success', description='Run finished successfully', finished=True),
            cls(id=cls.ERROR_ID, name='Error', description='Run terminated due to an error', finished=True),
            cls(id=cls.CANCELED_ID, name='Canceled', description='Run was canceled by user', finished=True)
        ]


class ScenarioRun(db.Model):
    __tablename__ = 'scenario_runs'
    __table_args__ = {'schema': RUN_SCHEMA}
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.ForeignKey(Scenario.id), nullable=False)
    ready_time = db.Column(db.DateTime(timezone=True), server_default=func.now())
    start_time = db.Column(db.DateTime(timezone=True))
    end_time = db.Column(db.DateTime(timezone=True))
    pathways_version = db.Column(db.Text())
    status_id = db.Column(db.ForeignKey(ScenarioRunStatus.id), server_default='1')
    pid = db.Column(db.Integer())

    scenario = db.relationship(Scenario, backref=db.backref('runs', order_by=ready_time.desc()))
    status = db.relationship(ScenarioRunStatus)


# Note that this table is stored in a "global" schema separate from other model content, in anticipation of a future
# where the same set of users will have access to multiple models, each stored in their own schema
class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': GLOBAL_SCHEMA}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    admin = db.Column(db.Boolean, server_default='false')

    scenarios = db.relationship(Scenario, backref='user')

    # A scenario is readable by a user if any of the following are true:
    # 1. The scenario is owned by the user
    # 2. The scenario is "built in" (owned by no user)
    # 3. The user is an admin (and can therefore read all scenarios)
    readable_scenarios = db.relationship(Scenario, primaryjoin=db.or_(id == Scenario.user_id,
                                                                      Scenario.user_id == None,
                                                                      admin == True))

    # Basic recipe for password hashing and checking is from http://exploreflask.readthedocs.io/en/latest/users.html
    @hybrid_property
    def password(self):
        return self.password_hash

    @password.setter
    def _set_password(self, plaintext):
        self.password_hash = bcrypt.generate_password_hash(plaintext)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self.password_hash, plaintext)

    def generate_auth_token(self, secret_key, expiration=3600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token, secret_key):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user

    def owns_scenario(self, scenario):
        # the check for not None here may be a little paranoid, but since "built-in" scenarios will have a None
        # user.id, we want to make sure we haven't passed in something that will accidentally match by virtue of
        # incorrectly having an empty id field
        return (self.id is not None and self.id == scenario.user_id) or self.admin

    def can_read_scenario(self, scenario):
        return scenario.is_built_in() or self.owns_scenario(scenario)

    def is_guest(self):
        return False


# Guest mimics User's interface for determining whether access to a given scenario should be allowed, but is not
# actually a User, so can't do anything *too* dangerous. Polymorphism!
class Guest(object):
    def owns_scenario(self, *args):
        return False

    def can_read_scenario(self, scenario):
        return scenario.is_built_in()

    @property
    def readable_scenarios(self):
        return Scenario.built_ins()

    def is_guest(self):
        return True


class OutputType(db.Model):
    __tablename__ = 'output_types'
    __table_args__ = {'schema': RUN_SCHEMA}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)

    # This provides a consistent way to set up the contents of the table whether migrating an existing database
    # or setting up a test database. Just do `session.add_all(OutputType.contents())` then commit the session.
    @classmethod
    def contents(cls):
        return [
            cls(id=1, name='Sankey - energy'),
            cls(id=2, name='Sankey - emissions'),
            cls(id=3, name='Energy demand'),
            cls(id=4, name='Annual cost'),
            cls(id=5, name='Emissions'),
            cls(id=6, name='Liquid fuels sectoral demand'),
            cls(id=7, name='Liquid fuels energy supply'),
            cls(id=8, name='Liquid fuels emissions intensity'),
            cls(id=9, name='Gaseous fuels sectoral demand'),
            cls(id=10, name='Gaseous fuels energy supply'),
            cls(id=11, name='Gaseous fuels emissions intensity'),
            cls(id=12, name='Electricity sectoral demand'),
            cls(id=13, name='Electricity energy supply'),
            cls(id=14, name='Electricity emissions intensity'),
            cls(id=15, name='Sales'),
            cls(id=16, name='Stocks'),
            cls(id=17, name='Service demand by tech'),
            cls(id=18, name='Energy by tech'),
            cls(id=19, name='Emissions by tech')
        ]


class Output(db.Model):
    __tablename__ = 'outputs'
    __table_args__ = {'schema': RUN_SCHEMA}

    id = db.Column(db.Integer, primary_key=True)
    scenario_run_id = db.Column(db.ForeignKey(ScenarioRun.id))
    output_type_id = db.Column(db.ForeignKey(OutputType.id))
    unit = db.Column(db.Text())

    scenario_run = db.relationship(ScenarioRun, backref=db.backref('outputs', lazy='dynamic'))
    output_type = db.relationship(OutputType)

    @property
    def output_type_name(self):
        return self.output_type.name


class OutputData(db.Model):
    __tablename__ = 'output_data'
    __table_args__ = {'schema': RUN_SCHEMA}

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.ForeignKey(Output.id))
    subsector = db.Column(db.ForeignKey(DemandSubsector.id))
    series = db.Column(db.Text())
    year = db.Column(db.Integer())
    value = db.Column(db.Float())

    output = db.relationship(Output, backref=db.backref('data', order_by=[subsector, series, year]))


