#!/usr/bin/python
import os

VENV_DIR = '/home/cloudcalc/server'
activate_this = os.path.join(VENV_DIR, 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))


os.environ['DATABASE_URL'] = 'mysql://cloudcalc:cloudcalc@localhost/cloudcalc'

from flup.server.fcgi import WSGIServer
from flask_APIdefinition import app

if __name__ == '__main__':
    WSGIServer(app).run()
