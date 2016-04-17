
from migrate.versioning import api
from config import WorkConfig
#from config import SQLALCHEMY_DATABASE_URI
#from config import SQLALCHEMY_MIGRATE_REPO
from flask_APIdefinition import db
import os.path
db.create_all()
print "Database: ", WorkConfig.SQLALCHEMY_DATABASE_URI
print "Migrate REPO: ", WorkConfig.SQLALCHEMY_MIGRATE_REPO
if not os.path.exists(WorkConfig.SQLALCHEMY_MIGRATE_REPO):
    api.create(WorkConfig.SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(WorkConfig.SQLALCHEMY_DATABASE_URI, WorkConfig.SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(WorkConfig.SQLALCHEMY_DATABASE_URI, WorkConfig.SQLALCHEMY_MIGRATE_REPO, api.version(WorkConfig.SQLALCHEMY_MIGRATE_REPO))
