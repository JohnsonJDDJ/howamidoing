import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db


bp = Blueprint('auth', __name__)

@bp.route('/create', methods=('GET', 'POST'))
def create():
    db = get_db()
    db.users.insert_one({"name" : "demo"})
    return "Hello World"


