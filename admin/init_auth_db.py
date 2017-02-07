#!/usr/bin/python
# -*- coding: utf-8 -*-

# init_tickets.py
#
# This file is used to populate the tickets database.
# It is called by the reset_db.sh script.
# Options for the sizes of the tables etc are included in
# options.py.

import json
import datetime
import random

from auth import User, DBSession, startup_info
from options import number_of_users

def load_names_from_json(name_root):
    f = open('json/' + name_root + '.json')
    names = json.loads(f.read()).keys()
    f.close()
    return names

def create_users(n):
    female_names = load_names_from_json('female_names')
    male_names = load_names_from_json('male_names')
    surnames = load_names_from_json('surnames')

    print "creating %d users" % n
    for i in range(n):
        first_name = random.choice(male_names + female_names)
        last_name = random.choice(surnames)
        name = '%s %s' % (first_name, last_name)
        email = first_name[0] + last_name + str(random.choice(range(10000,100000))) + '@gmail.com'
        picture = None
        session.add( User(
            name = name,
            email = email,
            picture = picture
        ))
    session.commit()

def populate_db():
    create_users(number_of_users)


if __name__ == '__main__':
    print startup_info
    session = DBSession()
    populate_db()
    session.close()
