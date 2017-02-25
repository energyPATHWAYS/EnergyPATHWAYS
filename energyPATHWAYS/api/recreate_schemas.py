# This script will re-create the "shared" and "public_runs" schemas (and their contents) that the API needs.
# Use this if you have a good copy of the "public" schema but are missing the others.

from flask import Flask
import models
import sqlalchemy.schema as schema
from getpass import getpass

# create the application object
app = Flask(__name__)
app.config.from_pyfile('config.py')
models.db.init_app(app)

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

    # Add foreign key from Scenarios to users
    models.db.engine.execute(schema.DDL('ALTER TABLE "Scenarios" ADD FOREIGN KEY(user_id) REFERENCES %s.users(id);' %
                                        (models.GLOBAL_SCHEMA,)))

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


