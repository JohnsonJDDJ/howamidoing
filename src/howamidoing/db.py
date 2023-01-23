import sqlite3

import click
from flask import current_app, g


def get_db():
    """
    Returns a database connection, which is 
    used to execute the commands read from the file
    """
    if 'db' not in g:
        # sqlite3.connect() establishes a 
        # connection to the file pointed at by 
        # the DATABASE configuration key.
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # sqlite3.Row tells the connection to return 
        # rows that behave like dicts. This allows 
        # accessing the columns by name.
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    # open_resource() opens a file relative to the 
    # flaskr package, which is useful since you 
    # won’t necessarily know where that location 
    # is when deploying the application later.
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


# click.command() defines a command line command 
@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    # Tells Flask to call that function 
    # when cleaning up after returning the response
    app.teardown_appcontext(close_db)
    # adds a new command that can be called 
    # with the flask command
    app.cli.add_command(init_db_command)