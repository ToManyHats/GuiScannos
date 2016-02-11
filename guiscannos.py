#!/usr/bin/python3
# -*- coding: utf-8 -*-

##########################################################################
##  GuiScannos provides an editor and log viewer for ppscannos output.
##  Copyright (C) 2016  Lisa Ann Hatfield
##
##  This file is part of GuiScannos.
##
##  GuiScannos is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  GuiScannos is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with GuiScannos.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################


"""
An editor and log viewer for use with ppscannos.py.
"""

import argparse, sys

from PyQt5.Qt import QApplication

from mainwin import MainWin


VERSION = '0.1'


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setOrganizationName('LHat')
    app.setApplicationName('Gui Scannos')
    app.setApplicationVersion(VERSION)
    
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='GUI for ppscannos.')

    #group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('srcfname', nargs='?', help='source filename')
    parser.add_argument('--version', action='store_true', default=False, help='display version information and exit')
    parser.add_argument('-l', '--log', dest='logfname', help='log filename')
    #parser.add_argument('-q', '--quiet', action='store_true', default=False, help='supress informational output')
    
    args = parser.parse_args()

    if args.version:
        print('guiscannos', VERSION)
        parser.exit()
       
    logname = None
    if args.logfname:
        logname = args.logfname
        
    w = MainWin(args.srcfname, logname)
    w.resize(700, 800)
    w.show()
    sys.exit(app.exec_())
