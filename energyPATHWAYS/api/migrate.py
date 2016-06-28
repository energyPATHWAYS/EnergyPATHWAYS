from flask import Flask
import models
import sqlalchemy.schema as schema
from getpass import getpass

# create the application object
app = Flask(__name__)
app.config.from_pyfile('config.py')
models.db.init_app(app)

# I admit to not really understanding why this is necessary, but it works around an error I was hitting, as described
# here: http://stackoverflow.com/questions/19437883/when-scattering-flask-models-runtimeerror-application-not-registered-on-db-w
with app.app_context():

    # The schema where we'll keep the "users" table so that it can be accessed from any future model schema
    models.db.engine.execute(schema.DDL('CREATE SCHEMA IF NOT EXISTS ' + models.GLOBAL_SCHEMA))
    models.User.__table__.create(bind=models.db.engine)

    # Add admin user
    pwd1 = pwd2 = ''
    while pwd1 != pwd2 or len(pwd1) < 8:
        pwd1 = getpass("Password for admin user (at least 8 char): ")
        pwd2 = getpass("Confirm password: ")
    admin = models.User(email='nowhere@example.com', name='admin', password=pwd1, admin=True)
    models.db.session.add(admin)
    models.db.session.commit()

    # Add description and user_id columns to Scenarios
    models.db.engine.execute(schema.DDL('ALTER TABLE "Scenarios" ADD COLUMN description TEXT'))
    models.db.engine.execute(schema.DDL('ALTER TABLE "Scenarios" ADD COLUMN user_id INTEGER REFERENCES %s.users (id)' %
                                        (models.GLOBAL_SCHEMA,)))

    # Add join tables for DemandCases/DemandCasesData and SupplyCases/SupplyCasesData
    models.demand_case_demand_case_data.create(bind=models.db.engine)
    models.supply_case_supply_case_data.create(bind=models.db.engine)

    # Move fks from original tables to join tables
    models.db.engine.execute('INSERT INTO "DemandCasesDemandCasesData" (demand_case_id, demand_case_data_id)'
                             'SELECT parent_id, id FROM "DemandCasesData"')
    models.db.engine.execute('INSERT INTO "SupplyCasesSupplyCasesData" (supply_case_id, supply_case_data_id)'
                             'SELECT parent_id, id FROM "SupplyCasesData"')

    # Remove original fk columns from case data tables
    models.db.engine.execute(schema.DDL('ALTER TABLE "DemandCasesData" DROP COLUMN parent_id'))
    models.db.engine.execute(schema.DDL('ALTER TABLE "SupplyCasesData" DROP COLUMN parent_id'))

    # Add description columns to case data tables
    models.db.engine.execute(schema.DDL('ALTER TABLE "DemandCasesData" ADD COLUMN description TEXT'))
    models.db.engine.execute(schema.DDL('ALTER TABLE "SupplyCasesData" ADD COLUMN description TEXT'))
    models.db.engine.execute('UPDATE "DemandCasesData" SET description = \'DemandCasesData description \' || id')
    models.db.engine.execute('UPDATE "SupplyCasesData" SET description = \'SupplyCasesData description \' || id')

    # Add schema for run info
    models.db.engine.execute(schema.DDL('CREATE SCHEMA IF NOT EXISTS ' + models.RUN_SCHEMA))

    # Add ScenarioRun and ScenarioRunStatus
    models.ScenarioRunStatus.__table__.create(bind=models.db.engine)
    models.db.session.add_all(models.ScenarioRunStatus.contents())
    models.db.session.commit()
    models.ScenarioRun.__table__.create(bind=models.db.engine)

    # Add tables to store outputs
    models.OutputType.__table__.create(bind=models.db.engine)
    models.db.session.add_all(models.OutputType.contents())
    models.db.session.commit()
    models.Output.__table__.create(bind=models.db.engine)
    models.OutputData.__table__.create(bind=models.db.engine)


