# project/__init__.py

import re
import datetime
import os
from flask import Flask, g, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import WorkConfig
from werkzeug import secure_filename
from flask import send_from_directory
from flask import request, jsonify, json


from model_cloudcalc import Base, User, Category, Specification, Gpl_line, Gpl   # database types
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import or_
#from project.textTokenizer import Tokenizer


# config
app = Flask(__name__, static_folder=WorkConfig.STATIC_FOLDER)
#if ('TESTING' in globals()):
#    app.config.from_object(TestConfig)
#else:
app.config.from_object(WorkConfig)
db = SQLAlchemy(app)

# Additional import
#from flask.ext.httpauth import HTTPBasicAuth
#auth = HTTPBasicAuth()

# static routes
#print "App static folder: ", app.static_folder


@app.route('/')
def index():
    print "App static folder: ", app.static_folder

    return app.send_static_file('index.html'), 200

@app.route('/<path:path>', methods=['GET'])
def static_site(path):
    return app.send_static_file(path), 200

''' ------------ API stuff begins
'''
## -------- tools -----
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

## --------- end -------

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('uploaded_file', filename=filename))
    return

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/api/specification', methods=['PUT'])
def send_spec_to_server():
    json_data = request.json

@app.route('/api/specification/<hash>', methods=['GET'])
def get_specification():
    pass


@app.route('/api/register', methods=['POST'])
def register():
    json_data = request.json
    user = User(
        name=json_data['name']

    )
    print ("new user: ", user)
    result={}
    try:
        db.session.add(user)
        db.session.commit()
        result['result'] = True
    except:
        result['result'] = False
        result['message'] = 'this user is already registered'
    db.session.close()
    return jsonify(result)



@app.route('/api/login', methods=['POST'])
def login():
    json_data = request.json
    try:
        user = db.session.query(User).filter(User.email == json_data['email']).one()
    except NoResultFound:
        print "Login API: NoResultFound exception while DB access"
        return jsonify({'result': False})
    except:
        print "Login API: unknown exception while DB access"
        return jsonify({'result': False})

    if user and user.checkPassword(json_data['password']):
        status = True
        resp = app.make_response(jsonify({'result': status, "userLogin" : user.email, "userToken" : user.get_token_string()}))
        resp.set_cookie('userLogin',value=user.email)
        resp.set_cookie('userToken', value=user.get_token_string())
        resp.set_cookie('userRole', value=str(user.role))
        print ("Server: REST API login: ", user.email, status)
    else:
        status = False
        resp = app.make_response(jsonify({'result': status, }))
    return resp


#@app.route('/logout', methods=['GET', 'POST'])
@app.route('/api/logout', methods=['POST'])
def logout():
    resp = app.make_response(jsonify({'result': 'success'}))
    resp.set_cookie('userLogin', '', expires=0)
    resp.set_cookie('userToken', '', expires =0)
    resp.set_cookie('userRole', '', expires =0)
    print ("Logging Response: ", resp)
    return resp


## -------------- Server start
if __name__ == '__main__':
    #import logging
    #logging.basicConfig(filename='flask-error.log',level=logging.DEBUG)
    print "App static folder: ", app.static_folder
    app.run()

