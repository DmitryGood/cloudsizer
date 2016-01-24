#!bin/python
import os
os.environ['DATABASE_URL'] = 'mysql://cloudcalc:cloudcalc@localhost/cloudcalc'

from flup.server.fcgi import WSGIServer
from flask_APIdefinition import app

if __name__ == '__main__':
    WSGIServer(app).run()
