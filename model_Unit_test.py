__author__ = 'slash'
import unittest
import hashlib
import os

from flask import Flask
from sqlalchemy import create_engine, and_, not_, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

#from project.models import User
from model_cloudcalc import Base, User, Category, Specification    # database types
from config import TestConfig
from flask import Flask
#from GPLFactory import GplFactory
from resourseProducts import ResourseFactory
from SpecFactory import SpecFactory

app = Flask(__name__)
app.config.from_object(TestConfig)

#engine = create_engine('sqlite:////')



class MyTest(unittest.TestCase):


    # ---------------------------------------------------------
    # ------------------- Helper procedures--------------------
    # ---------------------------------------------------------
    def populate_db(self):
        session = sessionmaker(bind=self.engine)()

        return


# ---------------------------------------------------------


    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        self.basedir = os.path.abspath(os.path.dirname(__file__))
        return app

    def setUp(self):

        # Create the engine. This starts a fresh database
        self.engine = create_engine('sqlite://')
        # Fills the database with the tables needed.
        # If you use declarative, then the metadata for your tables can be found using Base.metadata
        Base.metadata.create_all(self.engine)
        # Create a session to this database
        Base.metadata.bind = self.engine
        self.db=Base
        self.session = sessionmaker(bind=self.engine)()
        print " ----------- Starting new tests -------"
        print " --------------------------------------"

    def tearDown(self):

        self.session.close()
        #self.db.drop()


    def test_load_specification(self):

        user=User(name='User', role = User.USER_ROLE_USER)
        self.session.add(user)
        self.session.commit()

        self.basedir = os.path.abspath(os.path.dirname(__file__))
        print "Dir: ", self.basedir
        filename = self.basedir+'/data/BillOfMaterials_14714923.xls'
        spec_factory = SpecFactory(filename)
        self.assertTrue(spec_factory.hash !=None)
        hash = spec_factory.uploadSpecToDatabase(self.session,user)

        result = spec_factory.calculateSpecResources(self.session, hash)
        self.assertTrue(result.has_key('stat'))
        print 'Result', result['stat']

        self.assertTrue(rtresult.has_key('spec'))






