#!/usr/bin/env python
#
# Project:
#   glideinWMS
#
# File Version: 
#   $Id: checkFrontend.py,v 1.5 2011/02/10 21:35:31 parag Exp $
#
# Description:
#   Check if a glideinFrontend is running
# 
# Arguments:
#   $1 = work_dir
#
# Author:
#   Igor Sfiligoi
#

import sys,os.path
sys.path.append(os.path.join(sys.path[0],"../lib"))
import glideinFrontendPidLib

try:
    work_dir=sys.argv[1]
    frontend_pid=glideinFrontendPidLib.get_frontend_pid(work_dir)
except:
    print "Not running"
    sys.exit(1)

print "Running"
sys.exit(0)

