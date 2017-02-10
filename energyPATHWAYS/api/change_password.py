import click
from flask import Flask
import models

# create the application object
app = Flask(__name__)
app.config.from_pyfile('config.py')
models.db.init_app(app)

@click.command()
@click.argument('username')
@click.password_option()
def change_password(username, password):
    with app.app_context():
        user = models.User.query.filter_by(name=username).one()
        user.password = password
        models.db.session.commit()
        click.echo("Password successfully changed for user %s ." % (user.name,))

if __name__ == '__main__':
    change_password()