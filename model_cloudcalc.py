__author__ = 'slash'
from sqlalchemy import Column, String, Integer, ForeignKey, PickleType, Float, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import pickle
import datetime
import hashlib
from exceptions import ValueError
from flask import Flask
from config import BaseConfig


Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    ''' the table to store user

    '''
    USER_ROLE_ADMIN = 'admin'
    USER_ROLE_USER = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cookie = Column(String(100), nullable=False)
    name = Column(String(100))
    created = Column(DateTime, nullable=False)
    userdata = Column(PickleType)
    role = Column(String(20), nullable=False, default=USER_ROLE_USER)
    specifications = relationship('Specification', uselist=True)

    def __init__(self, name=None, role=USER_ROLE_USER, userdata=None):
        self.name = name
        self.role = role
        self.userdata = userdata
        self.created = datetime.datetime.now()
        # create cookie for user as hash of his first entrance time
        self.cookie = hashlib.sha1(str(self.created)).hexdigest() # create cookie for user as hash of his first entrance time
        return

    def getCookie(self):
        return self.cookie

class Specification(Base):
    __tablename__ = 'specification'
    ''' table to store user specifications
    '''

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime)
    filename = Column(String(250), nullable=False)
    name = Column(String(100))
    tokenized = Column(PickleType, nullable=False)
    hash = Column(String(100))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', uselist = False)

    def __init__(self, filename, name, tokenized, hash, user):
        self.filename = filename
        self.name = name
        self.tokenized = tokenized
        self.hash = hash
        self.user = user
        self.created = datetime.datetime.now()

# Tables to store pricelist
class Category(Base):
    __tablename__ = 'category'

    # product categories
    PROD_CPU = 'CPU'
    PROD_MEM = 'MEM'
    PROD_HDD = 'HDD'
    PROD_SSD = 'SDD'
    PROD_BUNDL = 'BUND'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    filter_list = Column(PickleType)
    filter_procedure = Column(PickleType)

    def __init__(self, name, filter_list):
        '''
        :param name: Category name
        :param filter_list:
        :return:
        '''
        self.name=name
        self.filter_list=filter_list


class Gpl_line(Base):
    __tablename__ = 'gpl_line'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pn = Column(String(50), nullable=False)
    description = Column(String(200), nullable=False)
    price = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship('Category', uselist = False)
    gpl_file_id = Column(Integer, ForeignKey('gpl.id'))
    gpl = relationship('Gpl', uselist = False)


class Gpl(Base):
    __tablename__ = 'gpl'
    ''' table for gpl file information
    '''
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    tag = Column(String(50), nullable=False)
    filename = Column(PickleType)
    gpl_lines = relationship('Gpl_line')
    created = Column(DateTime)

    def __init__(self, name, filename, tag):
        self.name = name
        self.filename = filename
        self.tag = tag
        self.created = datetime.datetime.now()
