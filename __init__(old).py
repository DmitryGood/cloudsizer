# project/__init__.py

import re
import datetime
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from config import WorkConfig, static_folder
from model_cloudcalc import Base, User, Category, Specification, Gpl_line, Gpl   # database types
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import or_
#from project.textTokenizer import Tokenizer

# config
app = Flask(__name__, static_folder=static_folder)
#if ('TESTING' in globals()):
#    app.config.from_object(TestConfig)
#else:
app.config.from_object(WorkConfig)
db = SQLAlchemy(app)

# Additional import
from flask import request, jsonify, json
#from flask.ext.httpauth import HTTPBasicAuth
#auth = HTTPBasicAuth()

# static routes

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>', methods=['GET'])
def static_site(path):
    return app.send_static_file(path)

''' ------------ API stuff begins
'''

@app.route('/api/specification', methods=['PUT'])
def send_spec_to_server():
    json_data = request.json


@app.route('/api/register', methods=['POST'])
def register():
    json_data = request.json
    user = User(
        email=json_data['email'],
        password=json_data['password']
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

@app.route('/api/textprocessing', methods=['POST'])
def text_processing():
    ''' Base test for text processing alghorithm
    :return:
    '''
    json_data = request.json
    name = json_data['name']
    if (name == None or name == ''):
        name = 'Test text'
    s=json_data['text']
    currpos = 0
    result=[]
    num=0
    lastPrefix = ""

    # Create checklist to filter text
    checklist = set()
    # Load base vocabulary to checklist
    try:
        base_voc = db.session.query(Vocabulary).filter(Vocabulary.shortcut == 'base').one()
    except:
        print "/api/textprocessing: can't load 'Base' vocabulary"
    else:
        for w in base_voc.words:
            checklist.add(w.word.upper())
    # Load most 1000 words to checklist
    try:
        voc1000 = db.session.query(Vocabulary).filter(Vocabulary.shortcut == '1000words').one()
    except:
        print "/api/textprocessing: can't load '1000words' vocabulary"
    else:
        for w in voc1000.words:
            checklist.add(w.word.upper())
    # Checklist id ready - start text processing
    wordDict ={}    # will be used to count unknown words
    # Start text
    for m in re.finditer("[A-Z|a-z|']+",s):
        word = {}
        if (m.group(0) == '-'):
            lastPrefix = lastPrefix + m.group(0)
            currpos = m.end()
            continue
        else:
            word['prefix']=lastPrefix+s[currpos:m.start()].strip()
            lastPrefix = ""
            word['word'] = m.group(0)
            currpos = m.end()
            while(currpos < len(s) and not s[currpos].isalpha() and s[currpos] != ' '):
                currpos +=1
            if (currpos != m.end()):
                word['ending'] = s[m.end():currpos]
        isKnown = (m.group(0).upper() in checklist)
        word['known'] = isKnown
        if (not isKnown):   #add word to wordList
            w = m.group(0).lower()
            if (wordDict.has_key(w)):       # the word is already in the list
                wordDict[w] += 1            # increase counter
            else:
                wordDict[w] = 1
        num +=1
        print "Parser", m.start(), m.end(), m.group()
        result.append(word)
    # Have to make WordList format for client side
    clientWordList = []
    for key in wordDict:
        w = {'word': key, 'quantity': wordDict[key], 'isName': False}
        clientWordList.append(w)

    resp = app.make_response(jsonify({'result' : True, 'data': { 'name' : name,
                                                                 'date' : datetime.datetime.now(),
                                                                 'content' : result,
                                                                 'wordlist': clientWordList}}))
    return resp, 200

@app.route('/api/voc', methods=['GET'])
def vocabulary_list():
    ''' API function /api/voc returns list of available vocabularies
        user check included,
            if user_role == admin, returns whole list,
            if user_role == user, just vocabulary for particular user
            if user isn't authenciated - returns empty list
        Inputs: sessionCookies = userToken to find is user authentified on not.
    :return: list of available vocabularies for user (for now language isn't being checked)
    '''
    user_token = request.cookies.get('userToken')
    if (user_token != None and verify_pw(user_token, "")):
        # we here only if user logged in and properly authenticated
        # user object should be stored in g.user property
        result=[]
        vocabularies = []
        if (g.user.role == User.USER_ROLE_ADMIN):
            # return full list of vocabularies

            vocabularies = db.session.query(Vocabulary).all()
        else:
            if (g.user.role == User.USER_ROLE_USER or g.user.role == User.USER_ROLE_TEACHER):
                # teachers now have the same rights like regular users
                # in fufture they will have access to all their student's vocabularies
                vocabularies = db.session.query(Vocabulary).filter(or_(Vocabulary.user_id == g.user.id, Vocabulary.is_system == True)).all()
        result=[]
        for v in vocabularies:
            r = {}
            r['id'] = v.id
            r['created'] = v.created_on
            r['name'] = v.name
            r['shortcut'] = v.shortcut
            r['lang'] = v.lang.sign
            r['system'] = v.is_system
            r['size'] = v.size
            if v.user != None:
                r['user'] = v.user.email
            result.append(r)
        resp = app.make_response(jsonify({'result' : True, 'data' : result}))
        return resp, 200
    else:
        return jsonify({'result': False}), 401

@app.route('/api/voc/<id>', methods=['GET'])
def vocabulary_get(id):
    ''' Return list of vocabulary words depending from vocabulary id
    :param id:
    :return:
    '''
    user_token = request.cookies.get('userToken')
    print "Check token for user: ", request.cookies.get('userLogin')
    if (user_token != None and verify_pw(user_token, "")):
        # we here only if user logged in and properly authenticated
        # user object should be stored in g.user property
        voc = db.session.query(Vocabulary).filter(Vocabulary.id == id).first()
        if (voc != None):   # if we found vocabulary
            # if user == admin OR user == owner of the vocabulary OR the vocabulary is system
            if (g.user.role == User.USER_ROLE_ADMIN or voc.user_id == g.user.id or voc.is_system):
                word_list = voc.words
                result = []
                for w in word_list:
                    r = {}
                    r['id'] = w.id
                    r['word'] = w.word
                    if (w.part_of_speech != None):
                        r['part_of_speech'] = w.part_of_speech
                    r['type'] = w.type
                    r['state'] = w.state
                    r['word_forms'] = w.word_forms
                    r['add_info'] = { 'picture' : 'icons/word-icon.png'}
                    result.append(r)
                resp = app.make_response(jsonify({'result' : True, 'data' : result}))
                return resp, 200
            else:    # if user not authorezed to work with vocabulary
                return jsonify({ 'result' : False}), 403
        else:       # if requested vocabulary is not found
            return jsonify({ 'result' : False}), 404
    else:           # if user is not authorized
        return jsonify({ 'result' : False}), 401

@app.route('/api/text', methods=['PUT'])
def putTextToDatabase():
    ''' This endpoint with PUT parameter adds text to database under specific user's account
    :return: text digest to find text
    '''
    # Get text data
    json_data = request.json
    text_name = json_data['name']
    text_content = json_data['text']
    # If text conten wrong - return error
    if (text_content == None or len(text_content) < 4):
        return jsonify({'result': False, 'message': 'Invalid text: too short!'}), 204   # 204 No Content
    # If text name is empty - give text name by the first sentence
    if (text_name == None, len(text_name) < 4):
        text_name = Tokenizer.produceTextName(text_content)

    # Check user token for authentication
    user_token = request.cookies.get('userToken')
    print "PUT text: Check token for user: ", request.cookies.get('userLogin')
    # create list of vocabularies to filter
    voc_list = ['base', '1000words']

    if (user_token != None and verify_pw(user_token, "")):
        print "User is authenticated, text saved for real user: ", g.user.email
        try:
            user_voc_id = db.session.Query(Vocabulary).filter(Vocabulary.user == g.user).one() # get user vocabulary
            voc_list.append(user_voc_id)
        except:
            print "Vocabulary for user %s is not found"%g.user.email
    else:
        print "User isn't authenticated, text saved for anonymous user.  "
        g.user=None

    # get user address
    try:
        remote_user_address = request.environ['REMOTE_ADDR']        # get user's IP address
    except:
        remote_user_address = None
    # and prepare other data
    text_hash = Tokenizer.getTextHash(text_content)             # make text hash
    # make check by hash in database for text duplicating

    tokenizer = Tokenizer(db.session, text_content, vocabularies=voc_list)  # creates Tokenizer object to tokenize the string
    text_tokens = tokenizer.getTokens()
    text_wordlist = tokenizer.getWordList()
    # create new text in database
    new_user_text = UserText(text_name, text_content, text_hash, text_tokens, text_wordlist, g.user, {'IP' : remote_user_address})
    db.session.add(new_user_text)
    db.session.commit()
    # return result & text hash
    resp = app.make_response(jsonify({'result': True, 'data' : text_hash}))
    return resp, 200

@app.route('/api/text/<hash>', methods=['GET'])
def getTextFromDatabase(hash):
    ''' This endpoint with GET parameter retrieve text from database to user
    :return: text object in 'data' field
    '''
    # Use text hash from request to load data from database
    try:
        textObject = db.session.query(UserText).filter(UserText.hash == hash).one()
    except:
        # If there is no text with such hash - return error # 204 No Content
        return jsonify({'result': False, 'message': 'No text. Please enter text'}), 204   # 204 No Content
    # Check user token for authentication
    user_token = request.cookies.get('userToken')
    print "GET text: Check token for user: ", request.cookies.get('userLogin')

    # ------ Start of authorization block
    if (user_token != None and verify_pw(user_token, "")):
        print "User is authenticated, check user permissions to the text: ", g.user.email
        if (g.user.role == User.USER_ROLE_ADMIN):
            # user is administrator have rights to retrieve any text
            pass
        elif (g.user.role == User.USER_ROLE_USER):
            # user is regular user - check ownership
            if textObject.user != g.user:
                textObject = None
        else:
            textObject = None
    else:
        print "User isn't authenticated, text loaded for anonymous user with hash "
        # Non-authenticated user can only load text from anonymous user with hash
        if textObject.user != None:
            textObject = None
    # If after authorization block textObject==None - authorization failed, return error
    if (textObject == None):
        # user doesn't have permissions to access this text # 403 Forbidden
        return jsonify({'result': False, 'message': "You don't have permissions to access this text"}), 403 # 403 Forbidden
    text_tokens = textObject.tokens
    text_wordlist = textObject.wordlist
    text_name = textObject.name
    text_created = textObject.created

    resp = app.make_response(jsonify({'result' : True, 'data': { 'name' : text_name,
                                                                 'date' : text_created,
                                                                 'content' : text_tokens,
                                                                 'wordlist': text_wordlist}}))
    return resp, 200

## -------------- Server start
if __name__ == '__main__':
    app.run()

