#!/usr/bin/python
# -*- coding: utf-8 -*-

# Flask libraries
from flask import Flask, render_template, request, redirect, Markup
from flask import jsonify, url_for, flash, make_response
from flask import session as app_session
from flask_seasurf import SeaSurf

# Standard python libraries
import httplib2, json, requests, random, string, os, sys
from functools import wraps
from dict2xml import dict2xml as xmlify

import imghdr
from werkzeug import secure_filename

# The auth database definitions are in auth-test.py
from auth-test import DBSession, User, createUser, getUserByEmail, getUserByID

app = Flask(__name__)

# Prevent cross-site request forgery
# Hidden '_csrf_token' fields have been added to the forms in the templates
# See https://flask-seasurf.readthedocs.org/en/latest/
csrf = SeaSurf(app)

db_session = DBSession()

from auth.google import Google_Auth_Client
from auth.facebook import Facebook_Auth_Client

import settings

auth_providers = {
    'google': Google_Auth_Client(settings.google_secrets_file),
    'facebook': Facebook_Auth_Client(settings.facebook_secrets_file)
}

DEBUG = True
LOG_ERRORS = True

#------------------------------------------------------------------------------------
# Helper function gen_response() is just a little wrapper around
# make_response() to make the code below more readable.
#
# TODO: this could do more, like have an error notification  page with 
# a 'Continue' button which would either take you to the main page
# or perhaps to where you were before the error.  Give it some thought.
#
def gen_response(msg, rc=401, content_type='application/json'):
    if DEBUG or LOG_ERRORS:
        print msg
    response = make_response(json.dumps(msg), rc)
    response.headers['Content-Type'] = content_type
    return response


#------------------------------------------------------------------------------------
# Authentication and Authorization View Decorators
# 
# We have here two view decorators: check_authentication() and
# auth_required() Each of them takes an arg 'msg' which is to be
# flashed.

# Function check_authentication() returns a decorator for wrapping
# those functions which require that the user be logged in.  If used,
# check_authentication() should be placed inside the app.route()
# decorator.
#
def check_authentication(msg):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in app_session:
                flash(msg)
                # The keyword arg 'next_url' is used in function login() 
                # in the call to redirect().  So we attempt the login and
                # then return to the page that required the login.
                return redirect(url_for('login', next_url=request.url))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Function check_authorization() returns a decorator for wrapping
# those functions that require authorized access. If used,
# check_authorization() should be placed inside the
# check_authentication() decorator.
#
def check_authorization(msg, item_class, end_point):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            item_id = kwargs['item_id']
            item = db_session.query(item_class).filter_by(id=item_id).one()
            if item.user_id != app_session['user_id']:
                flash(msg)
                return redirect(url_for(end_point, item_id=item_id))
            # We have already looked up the item so why have function f()
            # do it again?  So we have the following statement and we change
            # the endpoints that use this decorator to have the 'item' arg.
            # (I guess this makes the item_id arg superfluous.)
            kwargs['item'] = item
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_session_id():
    if not app_session.has_key('session_id'):
        app_session['session_id'] = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    return app_session.get('session_id')

#----------------------------------------------------------------------------------
# Auth Test App 

# login

class Login:

    def __init__(self, provider_name, access_token, access_id, user_data):
        self.provider_name = provider_name
        self.access_token = access_token
        self.access_id = access_id
        self.user_data = user_data

    def to_json(self):
        return json.dumps( {
            'provider_name': self.provider_name,
            'access_token': self.access_token,
            'access_id': self.access_id,
            'user_data': self.user_data } )

    def from_json(self, login_json):
        d = json.loads(login_json)
        self.provider_name = d['provider_name']
        self.access_token = d['access_token']
        self.access_id = d['access_id']
        self.user_data = d['user_data']

@app.route('/login')
def login():

    redirect_url = request.args.get('next_url') or url_for('conferences')
    session_id = get_session_id()

    # Facebook login
    fb_app_id = '907786629329598'
    fb_connect_js = Markup(render_template(
        'fb_connect.js',
        fb_app_id = fb_app_id,
        SESSION_ID = session_id,
        redirect_url = redirect_url
    ))

    # Google login
    google_app_id = auth_providers['google'].client_id
    google_connect_js = Markup(render_template(
        'google_connect.js',
        SESSION_ID = session_id,
        redirect_url = redirect_url
    ))

    return render_template(
        'login.html', 
        google_app_id = google_app_id,
        google_connect_js = google_connect_js,
        fb_connect_js = fb_connect_js,
        google_sign_in = True,
        app_session = app_session
    )


@csrf.exempt
@app.route('/connect/<provider_name>/<session_id>', methods=['POST'])
def connect(provider_name, session_id):

    # verify session_id
    if session_id != get_session_id():
        flash('Invalid session_id.')
        return redirect('/')

    # auth_code is in the 'POST' data
    auth_code = request.data
    login = auth_providers[provider_name].connect(auth_code, Login)

    if (app_session.get('login') is not None):
        prev_login = Login()
        prev_login.from_json(app_session.get('login'))
        if login.get('access_id') == prev_login.get('access_id'):
            msg = 'Current user is already connected.'
            flash(msg)
            return redirect(url_for('conferences'))
            
    user = getUserByEmail(db_session, login.user_data['email'])
    if not user:
        user = createUser(db_session, login.user_data)

    # Store the access token in the session for later use.
    app_session['login'] = login.to_json()
    app_session['user_id'] = user.id
    app_session['user_name'] = user.name

    msg = "you are now logged in as %s" % user.name
    flash(msg)
    return redirect('/')


# logout
#
@csrf.exempt
@app.route('/disconnect')
def disconnect():

    try:
        login_json = app_session.get('login')
        login = json.loads(login_json)
        provider = auth_providers[login.get('provider_name')]
        result = provider.disconnect(login)
        del app_session['login']
        del app_session['user_id']
        del app_session['user_name']
        msg = "You have successfully logged out."
        flash(msg)

    except:
        msg = "You are not logged in."
        flash(msg)

    return redirect(url_for('conferences'))


#---------------------------------------------------------------------------------------------
# User Views


@app.route('/users')
def users():
    users = db_session.query(User).all()
    return render_template('users.html', users=users)

@app.route('/users/<int:user_id>')
def ticket_user(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    main = Markup(render_template('user.html', user=user))
    return render_template('layout.html', main=main, app_session=app_session)

@app.route('/users/<int:user_id>/JSON')
def user_json(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    return jsonify(user.to_dict())

@app.route('/users/<int:user_id>/XML')
def user_xml(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    return xmlify(user.to_dict())


# generate a random secret key
app.secret_key = ''.join(random.choice(
    string.ascii_uppercase + string.digits) for x in xrange(32))

app.debug = False
print >> sys.stderr, 'auth app loaded.'
print >> sys.stderr, app

#---------------------------------------------------------------------------------------------
# Start the server

if __name__ == '__main__':
    print startup_info

    app.run(host='0.0.0.0', port=5000)
