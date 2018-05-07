#!/usr/bin/env python 

# -*- coding: utf-8 -*-
#
# remove_notes.py
#
##############################################################################
#
# Copyright (c) 2017 Juan Carlos Saez <jcsaezal@ucm.es>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import panflute as pf
import sys
import re
import os

# Add dummy imports for pyinstaller. These should probably belong in
# future since they are needed for pyinstaller to properly handle
# future.standard_library.install_aliases(). See
# https://github.com/google/rekall/issues/303
if 0:
	import UserList
	import UserString
	import UserDict
	import itertools
	import collections
	import future.backports.misc
	import commands
	import base64
	import __buildin__
	import math
	import reprlib
	import functools
	import re
	import subprocess

## Get language from metadata
def prepare(doc):
	return


def remove_notes(elem,doc):
	if isinstance(elem,pf.Div) and "notes" in elem.classes:
		return [] 
	elif isinstance(elem,pf.RawBlock) and elem.format=="html" and elem.text[0:4]=="<!--":
		return []	


def main(doc=None):
	#inputf = open('test.json', 'r')
	inputf=sys.stdin
	return pf.run_filters(actions=[remove_notes],doc=doc,input_stream=inputf)

if __name__ == "__main__":
	main()