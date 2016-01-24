__author__ = 'slash'

from sqlalchemy import Column, String, Integer, ForeignKey, PickleType, Float, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import pickle
import datetime
import bcrypt
from exceptions import ValueError

from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

from flask import Flask
from project.config import BaseConfig

#app = Flask(__name__)
#app.config.from_object(WorkConfig)

Base = declarative_base()

class Language(Base):
    __tablename__ = 'language'
    ''' This is table to store language name and additional information
        Additional information: description, etc.
    '''
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    sign = Column(String(5), nullable=False)
    icon = Column(String)

class PartOfSpeech(Base):
    __tablename__ = 'part_of_speech'
    ''' Table to store info about parts of speech
        Additional info: rules how to identify, etc.
    '''
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    sign = Column(String(5), nullable=False)
    add_info = Column(PickleType)

class Word(Base):
    __tablename__ = 'word'
    ''' Table to store vocabulary words
        Word is sequence of a-z,A-Z symbols which has meaning and translation
        word_forms - is a "picled" list of all possible forms of the word, including plural form, possessive, verb forms etc.
        type - is this word regular or some Name
        state - is this word DIRTY i.e. added by user, or CLEAR - checked by somebody
        add_info - correct writing for names, picture, pronunciation, transcription, etc,

        Constants - constants to use with class
    '''
    TYPE_REGULAR = 101        # regular word
    TYPE_NAME = 102           # personal name of someth.

    STATE_CLEAN = 201         # word's state: is it checked by moderator or added by user
    STATE_DIRTY = 202         # the word added to base by somebody

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime, nullable=False)
    word = Column(String, nullable=False)
    lang_id = Column(Integer, ForeignKey('language.id'), nullable=False)
    lang = relationship(Language)
    part_of_speech_id = Column(Integer, ForeignKey('part_of_speech.id'))
    part_of_speech = relationship(PartOfSpeech)
    type = Column(Integer, nullable=False, default=TYPE_REGULAR)
    state = Column(Integer, nullable=False, default=STATE_DIRTY)
    word_forms = Column(PickleType, nullable=True)
    add_info = Column(PickleType, nullable=True)
    translations = relationship('WordTranslation', secondary = 'word_translation')

    def __init__(self, word, lang, type=TYPE_REGULAR, state=STATE_DIRTY):
        self.word = word
        self.lang = lang
        self.type = type
        self.state = state
        self.created_on = datetime.datetime.now()

    def getWordForms(self):
        return self.word_forms

    def setWordForms(self, list):
        self.word_forms = list

class WordTranslation(Base):
    __tablename__ = 'translation'
    ''' Table to store word's translations
        Many-to-many relationship with words
        add_info - wikipedia link, picture link, usage cases (phrases)
    '''
    STATE_CLEAN = 201         # translation's state: is it checked by moderator or added by user/automatic tool
    STATE_DIRTY = 202         # the translation added to base by somebody

    id = Column(Integer, primary_key=True, autoincrement=True)
    dest_lang_id = Column(Integer, ForeignKey('language.id'), nullable=False)
    dest_lang = relationship(Language)
    translation = Column(String, nullable=False)
    add_info = Column(PickleType)
    description = Column(String)
    words = relationship('Word', secondary = "word_translation")
    state = Column(Integer, nullable=False, default=STATE_DIRTY)


class SingleVocabularyTranslation(Base):
    __tablename__ = 'word_translation'
    ''' Single translation for Vocabulary word.
        usage_factor = frequence of use of this particular word's translation
    '''
    STATE_CLEAN = 201         # relationship state: clear or DIRTY
    STATE_DIRTY = 202         # relationship added to base by somebody

    word_id = Column(Integer, ForeignKey('word.id'), primary_key=True)
    translation_id = Column(Integer, ForeignKey('translation.id'), primary_key=True)
    usage_factor = Column(Float, default=1)
    state = Column(Integer, nullable=False, default=STATE_DIRTY)

class Vocabulary(Base):
    __tablename__ = 'vocabulary'
    ''' Vocabulary as a collection of words. It's subset of all available words in the universe
        vocabulary can be system of belong to the particular user
        vocabulary contains links to words
        vocabulary contains filter - a sequence of words, using to filter user's text.
        vocabulary.size - number of words in vocabulary

    '''
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime, nullable=False)
    lang_id = Column(Integer, ForeignKey('language.id'), nullable=False)
    lang = relationship(Language)
    name = Column(String, default="Default vocabulary", nullable=False)
    shortcut = Column(String, default="new_voc")
    is_system = Column(Boolean, default=True, nullable=False)
    filter = Column(PickleType, nullable=False, default=pickle.dumps([]))
    is_filter_clean = Column(Boolean, default=True, nullable=False)
    size = Column(Integer, default=0, nullable=False)
    words = relationship('Word', secondary = 'vocabulary_words')
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', uselist = False)

    def __init__(self, name, lang, user=None, shortcut='default'):
        self.lang = lang
        if (user != None):
            self.is_system = False
        self.user = user
        self.created_on = datetime.datetime.now()
        self.name = name
        self.shortcut = shortcut


class VocabularyWords(Base):
    __tablename__ = 'vocabulary_words'
    ''' Many-to-many relationship table for vocabularies
        represents words, contained by particular vocabulary
        For user's vocabulary represents word, which particular user studies now.
        Word has status of studying.
    '''
    vocabulary_id = Column(Integer, ForeignKey('vocabulary.id'), primary_key=True)
    word_id = Column(Integer, ForeignKey('word.id'), primary_key=True)
    words = relationship(Word)

class User(Base):
    __tablename__ = "users"

    USER_ROLE_ADMIN = 1
    USER_ROLE_USER = 2
    USER_ROLE_TEACHER = 3

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    registered_on = Column(DateTime, nullable=False)
    role = Column(Integer, nullable=False, default=USER_ROLE_USER)
    isActive = Column(Boolean, nullable=False, default=False)
    username = Column(String)
    avatar = Column(String)
    settings = Column(PickleType)
    vocabulary = relationship('Vocabulary', uselist = False)        # to user with his vocabulary
    texts = relationship('UserText')                              # to connect User with his texts

    def __init__(self, email, password, role = USER_ROLE_USER):
        self.email = email
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())
        self.registered_on = datetime.datetime.now()
        self.role = role
        self.isActive = False

    def checkActive(self):
        return self.isActive

    def getId(self):
        return self.email

    def getName(self):
        return self.username

    def setActive(self, state = True):
        self.isActive = state
        return

    def checkPassword(self, password):
        return (bcrypt.hashpw(password, self.password)) == self.password

    def chagePassword(self, password):
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())
        return

    def generate_auth_token(self, expiration = 600):      # Which units used for expiration time?
            s = Serializer(secret_key=BaseConfig.SECRET_KEY, expires_in = expiration)
            token = s.dumps({ 'id': self.id })
            return token

    def get_token_string(self):
        return self.generate_auth_token().decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        '''
        :param token: user's token
        :return: user id from the token if the token is correct, None instead
        '''
        s = Serializer(BaseConfig.SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user_id = data['id']
        return user_id

    def hasVocabulary(self):
        '''
        :return: vocabulary id if available
        '''
        if not self.vocabulary:
            return False
        try:
            voc_id = self.vocabulary.id
        except:
            return False
        else:
            return voc_id

    def setVocabulary(self, vocabulary):

        if (not self.hasVocabulary()):
            try:
                self.vocabulary=vocabulary
            except:
                return False
            else:
                return True
        else:
            ''' User has vocabulary, we should shange it
            '''
            try:
                self.vocabulary.user_id = None
                self.vocabulary = vocabulary
            except:
                raise ValueError("Can't change vocabulary for user ")
            else:
                return True
    def getVocabulary(self):
        try:
            voc_id = self.vocabulary.id
        except:
            raise ValueError("Can't get vocabulary data ")
        else:
            return self.vocabulary


class UserText(Base):
    ''' Table to store texts, added by user
        name - Text name
        text - Text content
        hash - Text hash to find in future
        tokenized - tokenized version of text for future needs (changing vocabularies, etc.)
        user - owner of the text
        source_data - some data where is this text from.
                Example: IP-address, anonymous cookie, hyperlink, etc.
    '''
    __tablename__ = "usertext"
    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime, nullable=False)
    name = Column(String, nullable=False)
    text = Column(String, nullable=False)
    hash = Column(String, nullable=False)
    tokens = Column(PickleType, nullable=False)
    wordlist = Column(PickleType, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user=relationship("User", uselist=False)
    source_data = Column(PickleType)

    def __init__(self, name, text, hash, tokens, wordlist, user=None, source_data=None):
        self.name = name
        self.text = text
        self.hash = hash
        self.tokens = tokens
        self.wordlist = wordlist
        if user != None:
            self.user = user
        if source_data != None:
            self.source_data = source_data
        self.created = datetime.datetime.now()





