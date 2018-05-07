#!/usr/bin/env python 

# -*- coding: utf-8 -*-
#
# dual_md.py
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

from __future__ import print_function
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

def html_format(format):
	return format in ["html","html5","epub","epub3","revealjs","s5","slideous","slidy","dzslides"]

def latex_format(format):
	return format in ["latex","beamer"] 


def translate_string(raw_title,doc):
	if " ||| " not in raw_title and " ;;; " not in raw_title:
		return raw_title
	else:
		idxv=raw_title.find(" ||| ")

		if idxv==-1:
			idxv=raw_title.find(" ;;; ")	

		if doc.lang_id>=2:
			return raw_title[idxv+5:]
		else:
			return raw_title[0:idxv]


def translate_metainline(elem,doc):
##Pick language specific stuff
	tag_found=False
	right_content=[]
	left_content=[]
	for item in elem.content:
		if isinstance(item, pf.Str) and ( item.text=="|||" or item.text==";;;"):
			tag_found=True
		elif tag_found:
			right_content.append(item)
		else:
			left_content.append(item)

	if tag_found:
		if doc.lang_id>=2:
			right_content.pop(0) ## Remove first space
			elem.content=right_content
		else:
			elem.content=left_content[:-1] ## Remove space at the end

def str_to_metainline(raw_str):
	tokens=raw_str.split(" ")
	mi=pf.MetaInlines(pf.Str(tokens[0]))
	i=0
	for i in range(1,len(tokens)):
		mi.content.append(pf.Space)
		mi.content.append(pf.Str(tokens[i]))
	return mi

def default_vars(doc):
	if not "figureTitle" in doc.metadata:
		doc.metadata["figureTitle"]=str_to_metainline("Figura ||| Figure")
	if not "tableTitle" in doc.metadata:
		doc.metadata["tableTitle"]=str_to_metainline("Tabla ||| Table")
	if not "figPrefix" in doc.metadata:
		doc.metadata["figPrefix"]=str_to_metainline("figura ||| Figure")
	if not "tblPrefix" in doc.metadata:
		doc.metadata["tblPrefix"]=str_to_metainline("tabla ||| Table")		
	if not "eqnPrefix" in doc.metadata:
		doc.metadata["eqnPrefix"]=str_to_metainline("ec. ||| Eq.")
	if not "loftitle" in doc.metadata:
		doc.metadata["loftitle"]=str_to_metainline("# Lista de figuras ||| # List of figures")				
	if not "lotTitle" in doc.metadata:
		doc.metadata["lotTitle"]=str_to_metainline("# Lista de tablas ||| # List of tables")
	if (not "lang" in doc.metadata) and ("pandoc_lang" in doc.metadata):
		if isinstance(doc.metadata["pandoc_lang"],pf.MetaBool):
			if doc.metadata["pandoc_lang"].boolean:
				doc.metadata["lang"]=str_to_metainline("es ||| en")
		else:
			doc.metadata["lang"]=doc.metadata["pandoc_lang"]

## Critical vars only
def dual_vars(doc):
	yaml_vars=["title",
				"subtitle",
				"institute",
				"figureTitle",
				"eqnTitle",
				"tableTitle",
				"figPrefix",
				"tblPrefix",
				"loftitle",
				"lotTitle",
				"lang"]

	for yaml_var in yaml_vars:
		if yaml_var in doc.metadata:
			translate_metainline(doc.metadata[yaml_var],doc)
			#pf.debug(doc.metadata[yaml_var])


## Get language from metadata
def prepare(doc):
	##Load defaults	
	lang_dict={}
	lang_dict["lang1"]="SP"
	lang_dict["lang2"]="EN"
	lang_avail=["SP","EN"]
	lang_id=1 ## Fits

	lang1=doc.get_metadata('lang1')
	lang2=doc.get_metadata('lang2')

	## See if the user specified languages other than default 
	if lang1!=None:
		lang_dict["lang1"]=lang1
		lang_avail[0]=lang1
	if lang2!=None:
		lang_dict["lang2"]=lang2
		lang_avail[1]=lang2

	## Check user's choice 
	lang_enabled=doc.get_metadata('lang_enabled')

	if lang_enabled!=None:
		if lang_enabled=="1":
			doc.lang_str=lang_dict["lang1"]
			doc.lang_id=1
		elif lang_enabled=="2":
			doc.lang_str=lang_dict["lang2"]
			doc.lang_id=2
		else:	
			try:
				idx=lang_avail.index(lang_enabled)
			except:
				print(lang_enabled,"key not found in lang list", file=sys.stderr)
				exit(1)
			doc.lang_str=lang_enabled
			doc.lang_id=idx+1		
	else:
		doc.lang_str=lang_avail[0]	
		doc.lang_id=1


	## Tags to include/exclude stuff
	doc.include_begin="BEGIN-"+doc.lang_str
	doc.include_end="END-"+doc.lang_str

	if doc.lang_id==1:
		tag=lang_dict["lang2"]
	else:
		tag=lang_dict["lang1"]


	## Define some variables automatically (pandoc-crossref bridge code)
	default_vars(doc)

	## Deal with variable translation
	dual_vars(doc)

	doc.exclude_begin="BEGIN-"+tag
	doc.exclude_end="END-"+tag

	## Internal parameter
	doc.remove_component=False

	## Include for tex
	### IMPORTANT NOTICE: if the -H option of pandoc is used in the
	### Command line, then this will not take any effect whatsoever
	if doc.format=="latex" or doc.format=="beamer":

		if 'header-includes' in doc.metadata:
			includes=doc.metadata['header-includes']
			#pf.debug(type(includes))
			
		else:
			includes=pf.MetaList([])
			doc.metadata['header-includes']=includes
		cont=includes.content

		#for c in includes.content:
		#	pf.debug(c)
		#return

		cont.append(pf.MetaInlines(pf.RawInline('\n\\usepackage{comment}','tex')))

		cont.append(pf.MetaInlines(pf.RawInline('\n\\includecomment{in'+doc.lang_str+'}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\excludecomment{in'+tag+'}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\newcommand{\\dtext}[2]{#'+str(doc.lang_id)+'}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\newcommand{\\dcode}[2]{\\textcolor{NavyBlue}{#'+str(doc.lang_id)+'}}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\usepackage{tikz}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\usetikzlibrary{calc,backgrounds,arrows,shapes,matrix,fit,patterns,trees,positioning,decorations.pathreplacing,automata}','tex')))


def title_hacks(elem, doc):
	if isinstance(elem, pf.Header):
		#Filter out special attributes @[list_of_comma_separated_attr]@
		if len(elem.content)>=3 and isinstance(elem.content[0],pf.Cite) and isinstance(elem.content[1],pf.Str):
			print(elem.content[0].content[0].text, file=sys.stderr)
			# Remove also the space ...
			text_to_process=elem.content[0].content[0].text+elem.content[1].text

			## Remove @
			text_to_process=text_to_process.replace("@","")

			## Add classes
			row=re.split(r",",text_to_process)

			for item in row:
				elem.classes.append(item) 

			## Remove space if necessary
			if isinstance(elem.content[2],pf.Space):
				elem.content=elem.content[3:]
			else:
				elem.content=elem.content[2:]

			print(sys.stderr,elem.classes, file=sys.stderr, end="")

		##Pick language specific stuff
		tag_found=False
		right_content=[]
		left_content=[]
		for item in elem.content:
			if isinstance(item, pf.Str) and ( item.text=="|||" or item.text==";;;"):
				tag_found=True
			elif tag_found:
				right_content.append(item)
			else:
				left_content.append(item)

		if tag_found:
			if doc.lang_id>=2:
				right_content.pop(0) ## Remove first space
				elem.content=right_content
			else:
				elem.content=left_content[:-1] ## Remove space at the end
	if isinstance(elem, pf.TableCell):
		#pf.debug("Entra")
		##Pick language specific stuff
		#pf.debug(elem)
		for x in elem.content:
			tag_found=False
			right_content=[]
			left_content=[]
			for item in x.content:  
				if isinstance(item, pf.Str) and item.text==";;;":
					tag_found=True
				elif tag_found:
					right_content.append(item)
				else:
					left_content.append(item)
				#if not isinstance(item, pf.Space): 
				#	pf.debug(item.text)
			if tag_found:
				if doc.lang_id>=2:
					right_content.pop(0) ## Remove first space
					x.content=right_content
				else:
					x.content=left_content[:-1] ## Remove space at the end
	elif type(elem) == pf.Table:
		caption=elem.caption
		#pf.debug(caption)
		## No caption
		if len(elem.caption)==0: 
			return 
		last_item=caption[-1]
		crossref=False

		if type(last_item)==pf.Str and last_item.text.find("{")!=-1:
			del caption[-1] ## Delete it
			with_attributes=True
		else:
			with_attributes=False

		##Pick language specific stuff
		tag_found=False
		right_content=pf.ListContainer()
		left_content=pf.ListContainer()

		if not with_attributes:
			if latex_format(doc.format) and type(caption[0])==pf.RawInline:
				## Let's see if pandoc-crossref passed first
				right_content.append(caption[0])
				left_content.append(caption[0])
				del caption[0]
				#pf.debug(right_content)
				crossref=True
			elif html_format(doc.format) and len(caption)>=2 and type(caption[1])==pf.Str and caption[1].text[-1]==':':
				## Let's see if pandoc-crossref passed first
				right_content.append(caption[0])
				right_content.append(caption[1])
				left_content.append(caption[0])
				left_content.append(caption[1])
				del caption[0]				
				del caption[1]
				crossref=True

		for item in caption:
			#pf.debug(item)
			if isinstance(item, pf.Str) and ( item.text=="|||" or item.text==";;;"):
				tag_found=True
				continue
			if tag_found:
				right_content.append(item)
			else:
				left_content.append(item)

		if tag_found:
			if doc.lang_id>=2:
				if not crossref:
					right_content.pop(0) ## Remove first space
				if with_attributes:	
					right_content.append(last_item)
				elem.caption=right_content
			else:
				if with_attributes:	
					left_content.append(last_item)
				else:
					del left_content[-1] # Remove space at the end			
				elem.caption=left_content #
		#pf.debug(elem.caption)
		return None
	elif type(elem) == pf.Div:
			if "title" in elem.attributes:
				elem.attributes["title"]=translate_string(elem.attributes["title"],doc)	
	elif type(elem) == pf.Span: #and "dual" in attributes:
		##Pick language specific stuff
		tag_found=False
		right_content=[]
		left_content=[]
		for item in elem.content:
			if isinstance(item, pf.Str) and ( item.text=="|||" or item.text==";;;"):
				tag_found=True
			elif tag_found:
				right_content.append(item)
			else:
				left_content.append(item)
		if tag_found:
			if doc.lang_id>=2:
				right_content.pop(0) ## Remove first space
				elem.content=right_content
			else:
				elem.content=left_content[:-1] ## Remove space at the end


def filter_lang(elem, doc):
	#print(remove_component, elem.encode('utf-8'), file=sys.stderr)
	if isinstance(elem, pf.Para):
		if len(elem.content)!=1: 
			return None
		if not isinstance(elem.content[0], pf.Str):
			if doc.remove_component:
				return []
			else:
				return None	
		elif elem.content[0].text == doc.exclude_begin:
			doc.remove_component=True
			return []
		elif elem.content[0].text == doc.exclude_end:
			doc.remove_component=False
			return []
		elif elem.content[0].text == doc.include_begin:
			return []
		elif elem.content[0].text == doc.include_end:
			return []
		elif doc.remove_component:
			return []
	elif isinstance(elem, pf.Str) and (elem.text == doc.exclude_end):
		doc.remove_component=False
		return []		
	else:
		if doc.remove_component:
			return []
		else:
			return None

def dual_img(elem,doc):
	if isinstance(elem,pf.Image):
		## Hack title 
		tag_found=False
		right_content=[]
		left_content=[]
		for item in elem.content:  
			if not isinstance(item, pf.Space) and (item.text==";;;" or item.text=="|||"):
				tag_found=True
			elif tag_found:
				right_content.append(item)
			else:
				left_content.append(item)
		if tag_found:
			if doc.lang_id>=2:
				right_content.pop(0) ## Remove first space
				elem.content=right_content
			else:
				elem.content=left_content[:-1] ## Remove space at the end
		## Hack URL if .dual class
		if "dual" in elem.classes:
			url=elem.url
			## Skip regular URLS
			if not '://' in url:
				basename, file_extension = os.path.splitext(url)

				## Do not rename extensions if dual tikz figure
				if file_extension==".tex" and ("dtikz" in elem.classes) and (doc.format=="latex" or doc.format=="beamer"):
					return None
				tag="-%s" % doc.lang_str
				elem.url=basename + tag + file_extension
			

def main(doc=None):
	#inputf = open('test.json', 'r')
	inputf=sys.stdin
	return pf.run_filters(actions=[filter_lang,title_hacks,dual_img], doc=doc,input_stream=inputf,prepare=prepare)

if __name__ == "__main__":
	main()