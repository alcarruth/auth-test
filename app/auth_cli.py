#!/usr/bin/python -i
# -*- coding: utf-8 -*-

import sys, os
import settings

os.chdir(settings.app_dir)
sys.path.insert(0, settings.app_dir)

from auth_db import *

if __name__ == '__main__':

    import readline
    import rlcompleter
    readline.parse_and_bind("tab: complete")

    print startup_info

    session = DBSession()
    users = session.query(User).all()

    
