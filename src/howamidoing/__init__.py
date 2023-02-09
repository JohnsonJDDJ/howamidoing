__version__ = "0.0.1"

import os

from .objects import *
from .utils import *
from flask import Flask
from pymongo import MongoClient
from flask_pymongo import PyMongo



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/howamidoing"
    mongo = PyMongo(app)

    # # Register the db with the app so we can run
    # # `$ flask --app flaskr init-db`
    # # in the command line to initialize db
    # from . import db
    # db.init_app(app)

    # # Import and register the blueprint 'auth'
    # from . import auth
    # app.register_blueprint(auth.bp)

    # # Import and register the blueprint 'blog'
    # from . import blog
    # app.register_blueprint(blog.bp)
    # app.add_url_rule('/', endpoint='index')

    return app