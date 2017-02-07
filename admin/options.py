#!/usr/bin/python
# -*- coding: utf-8 -*-

# must match setting in reset_db.sh 
db_name = 'auth'

# db backend 
# either 'postgres' or 'sqlite' 
#engine_type = 'sqlite'
engine_type = 'postgres'

# options for dummy data creation
number_of_users = 1000
