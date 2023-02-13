__version__ = "0.0.1"

from .objects import *
from .utils import *
from flask import Flask

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/howamidoing"
    app.secret_key = "secret_key_value_goes_here"

    from . import auth
    app.register_blueprint(auth.bp)

    from . import profile
    app.register_blueprint(profile.bp)
    app.add_url_rule('/', endpoint='index')

    return app