from time import time
from app import db
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from datetime import datetime, timezone
import jwt
from .util import utcnow_tz

# Users and related configs
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean)
    results_per_page = db.Column(db.Integer, default=100)
    preview_length = db.Column(db.Integer, default=100)
    rescans = db.relationship('RescanTask', backref='submitter', lazy='select')

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_invite_token(self, expires_in=172800):
        return jwt.encode(
            {'invite_user': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_invite_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['invite_user']
        except:
            return
        return User.query.get(id)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Scope and blacklist items
class ScopeItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String, index=True, unique=True)
    blacklist = db.Column(db.Boolean, index=True)

    def getBlacklist():
        return ScopeItem.query.filter_by(blacklist=True).all()

    def getScope():
        return ScopeItem.query.filter_by(blacklist=False).all()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Server configuration options
class ConfigItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    type = db.Column(db.String(256))
    value = db.Column(db.String(256))
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# While generally I prefer to use a singular model name, each record here is going to be storing a set of services
class NatlasServices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sha256 = db.Column(db.String(64))
    services = db.Column(db.Text)

    def services_as_list(self):
        servlist = []
        idx = 1
        for line in self.services.splitlines():
            # any empty newlines will be skipped, or comment lines (for uploaded files)
            if line == '' or line.startswith('#'):
                continue

            # split on whitespace, store as tuple
            portnum = line.split()[1].split('/')[0]
            portproto = line.split()[1].split('/')[1]
            servlist.append((idx, portnum, portproto, line.split()[0]))
            idx += 1
        return servlist

    def as_dict(self):
        servdict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        servdict['as_list'] = self.services_as_list()
        return servdict


# Agent configuration options
class AgentConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    versionDetection = db.Column(db.Boolean, default=True)
    osDetection = db.Column(db.Boolean, default=True)
    defaultScripts = db.Column(db.Boolean, default=True)
    onlyOpens = db.Column(db.Boolean, default=True)
    scanTimeout = db.Column(db.Integer, default=300)
    webScreenshots = db.Column(db.Boolean, default=True)
    vncScreenshots = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class RescanTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime, index=True, default=utcnow_tz, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    target = db.Column(db.String, index=True)
    dispatched = db.Column(db.Boolean, default=False, index=True)
    date_dispatched = db.Column(db.DateTime, index=True)
    complete = db.Column(db.Boolean, default=False, index=True)
    date_completed = db.Column(db.DateTime, index=True)
    scan_id = db.Column(db.String, index=True, unique=True)

    def dispatchTask(self):
        self.dispatched = True
        self.date_dispatched = utcnow_tz()

    def completeTask(self, scan_id):
        self.scan_id = scan_id
        self.complete = True
        self.date_completed = utcnow_tz()

    @staticmethod
    def getPendingTasks(): # Tasks that haven't been completed and haven't been dispatched
        return RescanTask.query.filter_by(complete=False).filter_by(dispatched=False).all()

    @staticmethod
    def getDispatchedTasks(): # Tasks that have been dispatched but haven't been completed
        return RescanTask.query.filter_by(dispatched=True).filter_by(complete=False).all()

    @staticmethod
    def getIncompleteTasks(): #All tasks that haven't been marked as complete
        return RescanTask.query.filter_by(complete=False).all()

    @staticmethod
    def getIncompleteTaskForTarget(ip):
        return RescanTask.query.filter_by(target=ip).filter_by(complete=False).all()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}