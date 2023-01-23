__version__ = "0.0.1"

import os

from .objects import *
from .utils import *
from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'howamidoing.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register the db with the app so we can run
    # `$ flask --app flaskr init-db`
    # in the command line to initialize db
    from . import db
    db.init_app(app)

    # Import and register the blueprint 'auth'
    from . import auth
    app.register_blueprint(auth.bp)

    # Import and register the blueprint 'blog'
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app