#!/usr/bin/python -i
# -*- coding: utf-8 -*-

import json
from sqlalchemy import Column, ForeignKey, Integer, String, Date, create_engine, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, backref
from sqlalchemy.ext.hybrid import hybrid_property

import settings

Base = declarative_base()

#---------------------------------------------------------------
# User

class User(Base):
    __tablename__ = 'auth_user'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    picture = Column(String, nullable=True)

    def to_dict(self):
        d = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
        }
        if self.picture:
            d['picture'] = self.picture
        return {
            'db_table': self.__tablename__,
            'values': d
        }

    def __repr__(self):
        return "%s <%s>" % (self.name, self.email)

# add a user to the database
#
def createUser(db_session, user_data):
    user = User(
        name = user_data["name"],
        email = user_data["email"],
        picture = user_data["picture"]
    )
    db_session.add(user)
    db_session.commit()
    return user

# maps a user_id to a user
#
def getUserByID(db_session, user_id):
    try:
        return db_session.query(User).filter_by(id=user_id).one()
    except:
        return None

# lookup a user by their email address
# and return the user id
#
def getUserByEmail(db_session, email):
    try:
        return db_session.query(User).filter_by(email=email).one()
    except:
        return None

#---------------------------------------------------------------

# For postgresql the db user will be the user asssociated with the
# current python process.  See postgresql configuration files pg_hba.conf
# and pg_ident.conf for more information.
#
db_urls = {
    'postgres': 'postgresql:///%s' % settings.db_name,
    'sqlite': 'sqlite:///%s.db' % settings.db_name
}
engine = create_engine(db_urls[settings.engine_type])
Base.metadata.create_all(engine)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

def engine_version():
    if settings.engine_type == 'postgres':
        from psycopg2 import __version__
        return 'psycopg2 (%s)' % __version__
    if settings.engine_type == 'sqlite':
        from sqlite3 import version
        return 'SQLite3 (%s)' % version

def set_prompt(ps):
    sys.ps1 = "\n%s->>> " % ps
    sys.ps2 = " " * len(str(ps)) +  " ... "

# set_prompt(settings.db_name)

def alchemy_version():
    from sqlalchemy import __version__
    return 'SQL Alchemy (%s)' % __version__

startup_info = "Auth Test\n" + str(engine) + '\n'

