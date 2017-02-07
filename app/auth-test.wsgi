#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os

app_dir = '/home/carruth/auth-test/app'
os.chdir(app_dir)
sys.path.insert(0, app_dir)

import settings

from auth_web import app as application
