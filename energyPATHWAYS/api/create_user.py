import click
from flask import Flask
import models

# create the application object
app = Flask(__name__)
app.config.from_pyfile('config.py')
models.db.init_app(app)

@click.command()
@click.option('-a', '--admin/--no_admin', default=False, help="Should user have administrative privileges?")
@click.password_option()
@click.argument('username')
@click.argument('email')
def create_user(admin, password, username, email):
    with app.app_context():
        new_user = models.User(email=email, name=username, password=password, admin=admin)
        models.db.session.add(new_user)
        models.db.session.commit()
        desc = "Admin user" if new_user.admin else "User"
        click.echo("%s %s created with id %i." % (desc, new_user.name, new_user.id))

if __name__ == '__main__':
    create_user()