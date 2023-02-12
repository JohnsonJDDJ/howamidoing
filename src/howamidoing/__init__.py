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

    from . import demo
    app.register_blueprint(demo.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    return app