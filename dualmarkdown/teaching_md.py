#!/usr/bin/env python 

# -*- coding: utf-8 -*-
#
# teaching_md.py
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
import copy
import unicodedata

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
	

class Dimension:
	def __init__(self,str):
		self.str=str
		if "%" in str:
			self.width=float(str[0:-1])
			self.units="%"
		elif ("px" in str) or ("em" in str) or  ("cm" in str) or ("mm" in str) or ("pt" in str):			
			self.width=float(str[0:-2])
			self.units=str[-2:] ## Get last two characters of the string
		else:
			self.width=50.0
			self.units="%"

	def to_latex(self):
		if self.units=="%":
			return  "{:.3f}".format(self.width/100.0)+"\\textwidth"
		else:
			return self.str.replace("px","pt")	

	def to_html(self):
		return self.str.replace("pt","px")		


def html_format(format):
	return format in ["html","html5","epub","epub3","revealjs","s5","slideous","slidy","dzslides"]

def latex_format(format):
	return format in ["latex","beamer"] 

## Get language from metadata
def prepare(doc):
	doc.exercisecount = 0 ## Added attribute!!
	doc.inside_exercise=False
	doc.questioncount = 0 ## Added attribute!!
	doc.inside_question=False
	doc.column_count=0
	doc.columns_width=Dimension("600pt")
	doc.columns_sep=Dimension("0cm")
	doc.columns_to_patch=[]
	doc.prev_column=None
	doc.enable_traditional_tables=False
	doc.disable_columns=True
	doc.custom_counters={}

	#print >> sys.stderr, doc.format 
	if doc.api_version==(1,17,0,4):
		doc.disable_columns=False
	
	doc.pandoc_columns=doc.get_metadata('pandoc_columns', default=False, builtin=True)
	tables = doc.get_metadata('traditional-tables', default=False, builtin=True)
	doc.autounderlined=doc.get_metadata('autounderlined', default=False, builtin=True) and latex_format(doc.format)
	framed_on=doc.get_metadata('includeframed', default=True, builtin=True) and latex_format(doc.format)
	doc.embed_pdfnotes=doc.get_metadata('embed_pdfnotes', default=False, builtin=True) and doc.format=="beamer"
	doc.note_counter=1

	if tables:
		doc.enable_traditional_tables=tables

	if doc.format=="latex" or doc.format=="beamer":

		if 'header-includes' in doc.metadata:
			includes=doc.metadata['header-includes']			
		else:
			includes=pf.MetaList([])
			doc.metadata['header-includes']=includes
		cont=includes.content
		## TIKZ
		cont.append(pf.MetaInlines(pf.RawInline('\n\\usepackage{tikz}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\usetikzlibrary{calc,backgrounds,arrows,shapes,matrix,fit,patterns,trees,positioning,decorations.pathreplacing,automata}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\usepackage{standalone}','tex')))
		cont.append(pf.MetaInlines(pf.RawInline('\n\\usepackage{color}','tex')))
		#Shaded enviroments
		if framed_on:
			cont.append(pf.MetaInlines(pf.RawInline('\n\\usepackage{framed,color}','tex')))
			cont.append(pf.MetaInlines(pf.RawInline('\n\\definecolor{shadecolor}{gray}{0.9}','tex')))
			cont.append(pf.MetaInlines(pf.RawInline('\n\\definecolor{gray}{rgb}{0.5,0.5,0.5}','tex')))
			cont.append(pf.MetaInlines(pf.RawInline('\n\\usepackage{framed}','tex')))

		#if doc.embed_pdfnotes:
		#	cont.append(pf.MetaInlines(pf.RawInline(r'\usepackage[final]{pdfpages}','tex')))
		#	cont.append(pf.MetaInlines(pf.RawInline(r'\usepackage{pgfpages}','tex')))
		#	cont.append(pf.MetaInlines(pf.RawInline(r'\setbeameroption{show notes on second screen=bottom}','tex'))) #  on second screen=bottom}
			#cont.append(pf.MetaInlines(pf.RawInline(r'\setbeamertemplate{note page}{\pagecolor{yellow!5}\vfill\insertnote\vfill}','tex')))
			


def lbegin_lend(elem, doc):
	if isinstance(elem,pf.RawInline) and elem.format==u'tex':
		if re.match('^\\\\lbegin\{.*\}.*$',elem.text) or re.match('^\\\\lend\{.*\}.*$',elem.text):
			new_text=elem.text.replace("lbegin","begin").replace("lend","end")
			return [pf.RawInline(new_text,elem.format)]
	elif isinstance(elem,pf.RawBlock) and elem.format==u'tex':
		if re.match('^\\\\lbegin\{.*\}.*$',elem.text) or re.match('^\\\\lend\{.*\}.*$',elem.text):
			new_text=elem.text.replace("lbegin","begin").replace("lend","end")
			return [pf.RawBlock(new_text,elem.format)]


# Right. Then we'd need something like:
# 
# <div class="columns">
# <div class="column">
# - my
# - pros
# </div>
# <div class="column">
# - my
# - cons
# </div>
# </div>


def columns(elem,doc):
	## Desactivar para pandoc nuevo		
	if type(elem) == pf.Div and 'columns' in elem.classes and not doc.pandoc_columns:
		## Eliminar de elem.classes
		if doc.disable_columns:
			elem.classes.remove('columns')
		doc.column_count=0
		doc.prev_column=None
		#pf.debug("Entra")
		## Process column attributes
		if "width" in elem.attributes:
			doc.columns_width=Dimension(elem.attributes["width"])
		else:
			doc.columns_width=Dimension("600px")

		if "colsep" in elem.attributes:
			doc.columns_sep=Dimension(elem.attributes["colsep"])
		else:
			doc.columns_sep=Dimension("0pt")

		to_patch=doc.columns_to_patch ## Keep track of object
		doc.columns_to_patch=[] ## Clean columns to patch
		if doc.format == 'beamer':
			left = pf.RawBlock('\\begin{columns}', format='latex')
			right = pf.RawBlock('\\end{columns}', format='latex')
			if doc.columns_sep.width!=0:
				rep_text='\\hspace{'+doc.columns_sep.to_latex()+'}'
			else:
				rep_text='% no sep'
			for col in to_patch:
				col.text=col.text.replace("COLSEP",rep_text)
			elem.content = [left] + list(elem.content) + [right]
			return elem
		elif html_format(doc.format): 
			elem.attributes["style"]="style=width:"+doc.columns_width.to_html()+";margin:0 auto;line-break-after: always;"
			#elem.content = list(elem.content) + [pf.RawBlock('<br/>', format='html')]
			if doc.columns_sep.width!=0:
				rep_text=doc.columns_sep.to_html()
			else:
				rep_text='2px'
			#Patch column HTML attributes
			for col in to_patch:
				col.attributes["style"]=col.attributes["style"].replace("COLSEP",rep_text)
			return [elem,pf.RawBlock('<br style=\"clear:both\"/>', format='html')]
		elif doc.format == 'latex':
			left = pf.RawBlock('\\begin{center}', format='latex')
			right = pf.RawBlock('\\end{center}', format='latex')
			if doc.columns_sep.width!=0:
				rep_text='\\hspace{'+doc.columns_sep.to_latex()+'}%\n'
			else:
				rep_text=''
			for col in to_patch:
				col.text=col.text.replace("COLSEP",rep_text)
	
			elem.content = [left] + list(elem.content) + [right]
			return
		elif doc.format == 'docx':
			row=pf.TableRow()
			for col in to_patch:
				row.content.append(col)
			rows=[row]
			return pf.Table(*rows)	
		else:
			return
	elif type(elem) == pf.Div and 'column' in elem.classes and not doc.pandoc_columns:
		## Eliminar de elem.classes
		if doc.disable_columns:
			elem.classes.remove('column')
		doc.column_count=doc.column_count+1
		if "width" in elem.attributes:
			width=Dimension(elem.attributes["width"])
		else:
			width=Dimension("50%")

		if doc.format == 'beamer':
			left = pf.RawBlock('\\begin{column}{'+width.to_latex()+'}', format='latex')
			right = pf.RawBlock('\\end{column}', format='latex')
			if doc.column_count>1:
				rb=pf.RawBlock('COLSEP', format='latex')
				doc.columns_to_patch.append(rb)
				elem.content = [rb] + [left] + list(elem.content) + [right] 
			else:
				elem.content = [left] + list(elem.content) + [right] 		
			return elem		
		elif html_format(doc.format): 
			if doc.column_count>1:
				fval="left" #"right" 
			else:
				fval="left"
			elem.attributes["style"]="style=width:"+width.to_html()+";float:"+fval+';margin-right:COLSEP';
			doc.columns_to_patch.append(elem)
			return
		elif doc.format == 'latex':
			if doc.prev_column==None:
				left=pf.RawBlock('\\begin{minipage}{'+width.to_latex()+'}', format='latex')
				right=pf.RawBlock('\\end{minipage}', format='latex')
				elem.content = [left] + list(elem.content) + [right]
			else:
				closing_minipage=doc.prev_column.content[-1] ## Last item ... 
				closing_minipage.text='\\end{minipage} %\nCOLSEP\\begin{minipage}{'+width.to_latex()+'}'
				right=pf.RawBlock('\\end{minipage}', format='latex')
				doc.columns_to_patch.append(closing_minipage)
				elem.content =  list(elem.content) + [right]
			doc.prev_column=elem
			return elem	
		elif doc.format == 'docx':
			obj=pf.TableCell(*elem.content)
			doc.columns_to_patch.append(obj)
			return elem
		else:
			return



def pagebreaks(elem,doc):
	## New way (not supported yet)
	# ------- {.pagebreak}
	#if type(elem) == pf.HorizontalRule and 'pagebreak' in elem.classes:
	if type(elem) == pf.Header and 'pagebreak' in elem.classes:
		if doc.format == "latex":
			return [pf.RawBlock('\\pagebreak[4]', format='latex')]
		elif doc.format == "beamer":
			return [pf.RawBlock('\\framebreak', format='latex')]
		elif html_format(doc.format):  
			return [pf.RawBlock("<div style=\"page-break-after: always;\"></div>", format='html')]
		elif doc.format == "docx": 
			## TODO: docx raw code not supportted for now
			## This does not work yet ... 	
			return [pf.RawBlock("<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>", format='openxml')]
		else:
			return []
	elif type(elem) == pf.Header and 'framebox' in elem.classes:
		if "width" in elem.attributes:
			height=Dimension(elem.attributes["width"])
		else:
			height=None
		if doc.format == "latex" or doc.format == "beamer":
			if height==None:
				return [pf.RawBlock('\\noindent\\framebox[\\textwidth]{\\rule{0pt}{4cm}}', format='latex')]
			else:
				return [pf.RawBlock('\\noindent\\framebox[\\textwidth]{\\rule{0pt}{'+height.to_latex()+'}}', format='latex')]
		elif html_format(doc.format):  
			if height==None:
				return [pf.RawBlock("<div style=\"border: 1px solid black;height:300px\"></div>", format='html')]
			else:
				return [pf.RawBlock("<div style=\"border: 1px solid black;height:"+height.to_html()+"\"></div>", format='html')]
		elif doc.format == "docx": 
			if height==None:
				siz="2000"
			else:
				siz=height.width
			return [pf.RawBlock(r'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="8659" w:type="dxa"/></w:tblPr><w:tblGrid><w:gridCol w:w="8659"/></w:tblGrid><w:tr><w:trHeight w:val="'+siz+'" w:hRule="exact"/><w:tc><w:p><w:r><w:t>AAA</w:t></w:r></w:p></w:tc></w:tr></w:tbl>',format='openxml')]
	elif type(elem) == pf.HorizontalRule and latex_format(doc.format):
		## Half-width rules replaced width full width rules
		return [pf.RawBlock(r'\hrulefill',format='latex')]


def removeAccents(string):
	nfkd_form = unicodedata.normalize('NFKD', string)
	return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def toIdentifier(string):
	# replace invalid characters by dash
	string = re.sub('[^0-9a-zA-Z_-]+', '-', removeAccents(string.lower()))

	# Remove leading digits
	string = re.sub('^[^a-zA-Z]+', '', string)

	return string


def custom_span(elem,doc):
	if type(elem) == pf.Span:
		## Simple numbering is format independent (deal with these first)
		items=elem.content
		#sys.stderr.write(pf.stringify(elem))
		if len(items) >= 3 and isinstance(items[-2],pf.Space) and isinstance(items[-1],pf.Str):
			number_marker=items[-1].text
			if number_marker=='#':
				id_item=toIdentifier(pf.stringify(elem))
				
				if id_item in doc.custom_counters:
					number=doc.custom_counters[id_item]
					doc.custom_counters[id_item]=number+1
				else:
					number=1
					doc.custom_counters[id_item]=2

				if "reset" in elem.classes:
					number=1
					doc.custom_counters[id_item]=1

				elem.content=list(items[:-2])+[pf.Space(),pf.Str(text=str(number))]
				return elem

		if doc.format == "beamer":
			for eclass in elem.classes:
				if eclass=="underline" or eclass=="alert": 
					elem.content = [pf.RawInline('\\%s{' % eclass, format='latex')] + list(elem.content) + [pf.RawInline('}', format='latex')]
			if "color" in elem.attributes:
				elem.content = [pf.RawInline('\\textcolor{%s}{' % elem.attributes["color"], format='latex')] + list(elem.content) + [pf.RawInline('}', format='latex')]
		elif doc.format ==  "latex":
			for eclass in elem.classes:
				if eclass=="underline": 
					elem.content = [pf.RawInline('\\%s{' % eclass, format='latex')] + list(elem.content) + [pf.RawInline('}', format='latex')]
				elif eclass=="alert":
					elem.content = [pf.RawInline('\\textcolor{red}{', format='latex')] + list(elem.content) + [pf.RawInline('}', format='latex')]
				if "color" in elem.attributes:
					elem.content = [pf.RawInline('\\textcolor{%s}{' % elem.attributes["color"], format='latex')] + list(elem.content) + [pf.RawInline('}', format='latex')]
		elif html_format(doc.format): 
			for eclass in elem.classes:
				if eclass=="underline": 
					elem.content = [pf.RawInline('<span style=\"text-decoration: underline\">', format='html')] + list(elem.content) + [pf.RawInline('</span>', format='html')]
				elif eclass=="alert":
					elem.content = [pf.RawInline('<span style=\"color:red\">', format='html')] + list(elem.content) + [pf.RawInline('</span>', format='html')]
			if "color" in elem.attributes:

				color=elem.attributes["color"]
				del elem.attributes["color"]
				if "style" in elem.attributes:
					elem.attributes["style"]+=";color:"+color
				else:
					elem.attributes["style"]="color:"+color
		elif doc.format== "docx":
			##TODO
			#See xhttp://officeopenxml.com/WPtextFormatting.php
			for eclass in elem.classes:
				if eclass=="underline": 
					elem.content = [pf.RawInline('<w:r><w:rPr><w:u/></w:rPr>', format='openxml')] + list(elem.content) + [pf.RawInline('</w:r>', format='openxml')]
				elif eclass=="alert":
					elem.content = [pf.RawInline('<w:r><w:rPr><w:color w:val="FF0000"/></w:rPr>', format='openxml')] + list(elem.content) + [pf.RawInline('</w:r>', format='openxml')]
	return None


supported_fontsizes={"tiny":50 , "scriptsize":70 , "footnotesize":80 , "small":90 , "normalsize":100 , "large":120 , "Large":140 , "LARGE":170 , "huge":200 , "Huge":250 }

def create_raw_item(span,str,format):
	if span:
		return pf.RawInline(str,format)
	else:
		return pf.RawBlock(str,format)		

def custom_fontsize(elem,doc):
	if (type(elem) == pf.Span or type(elem) == pf.Div) and ("fontsize" in elem.attributes):
		is_span=(type(elem) == pf.Span)
		fsize=elem.attributes["fontsize"]
		del elem.attributes["fontsize"]
		if latex_format(doc.format):
			if fsize in supported_fontsizes:
				left=create_raw_item(is_span,'{\\'+fsize+' ' , format='latex')
				right=create_raw_item(is_span,'}', format='latex')
				elem.content = [left] + list(elem.content) + [right]
				return None
			else:
				## Case for fontsize{8}{9} \selectfont
				size_vals=fsize.split(',')

				if len(size_vals)==2:
					left=create_raw_item(is_span,'{\\fontsize{'+size_vals[0]+'}{'+size_vals[0]+'}\\selectfont ', format='latex')
					right=create_raw_item(is_span,'}', format='latex')
					elem.content = [left] + list(elem.content) + [right]
					return None		

		elif html_format(doc.format):
			if fsize in supported_fontsizes:
				size_pct=supported_fontsizes[fsize]
				
				if "style" in elem.attributes:
					elem.attributes["style"]+=';font-size:'+str(size_pct)+'%'+align
				else:
					elem.attributes["style"]='font-size:'+str(size_pct)+'%'	

		elif doc.format== "docx":
			##TODO
			return None


def hack_table(orig_input):
	try:

		# Important group being saved: the r, c, or l's for the table columns.
		#                                                        vvvvvvvv
		vert_re = re.compile(r'(\\begin\{longtable\}\[.*\]\{@\{\})([rcl]+)(@\{\}\})', re.MULTILINE)
		#                                             ^ not sure if pandoc changes this ever?
		# We have three groups captured above:
		#
		# 1. \begin{longtable}[c]{@{}
		# 2. [rcl]+
		# 3. @{}}
		#
		# The below takes these three, turns group 2 into vertically separated columns, and
		# then appends this to `replacements` joined with 1 and 3 so we can use `sub` below.
		replacements = []
		for match in vert_re.finditer(orig_input):
			table_start, cols, table_end = match.groups()
			# Gives you say |r|c|l|
			# If you forever wanted just r|c|l without the outer ones, set vert_cols to just
			# be "|".join(cols).  Get creative if you don't want every inner one vertically
			# separated.
			vert_cols = "|{}|".format("|".join(cols))
			replacements.append("{}{}{}".format(table_start, vert_cols, table_end))

		# probably not necessary
		output = copy.deepcopy(orig_input)

		# if the above loop executed, the same regex will have the matches replaced
		# according to the order we found them above
		if replacements:
			output = vert_re.sub(lambda cols: replacements.pop(0), output)

	    # Set this to True if pandoc is giving you trouble with no horizontal rules in
	    # tables that have multiple rows
		if False:
			output = re.sub(r'(\\tabularnewline)(\s+)(\\begin{minipage})', r'\1\2\\midrule\2\3', output)


		## Replace \midrule \toprule \bottomrule -> <nothing> 
		## Replace \tabularnewline -> \tabularnewline \hline 
		output = re.sub(r'(\\midrule|\\bottomrule|\\toprule)', '',output)
		output = re.sub(r'(\\tabularnewline)', r'\\tabularnewline \\hline',output)
	    # write the conversion to stdout
	    #sys.stdout.write(output)
		return output
	except Exception as e:
	    # you may want to change this to fail out -- if an error was caught you probably
	    # aren't going to actually get any valid output anyway?  up to you, just figured
	    # i'd write something *kind of* intelligent.
	    sys.stderr.write(
	        "Critical error, printing original stdin to stdout:\n{}".format(e)
	    )
	    #sys.stdout.write(orig_input)

def table_separators(elem,doc):
	if isinstance(elem,pf.Table) and doc.enable_traditional_tables:
		if latex_format(doc.format):
			doc.metadata['tables']=True
			raw_item=pf.convert_text(elem, input_format='panflute', output_format='latex')
			print("raw_item", file=sys.stderr)
			#pf.debug(hack_table(raw_item))
			return [pf.RawBlock(hack_table(raw_item),'latex')] 
		elif html_format(doc.format):
			raw_item=pf.convert_text(elem, input_format='panflute', output_format='html')
			raw_item=raw_item.replace('<table>','<table style=\'border-collapse: collapse; border: 1px solid black\'>')
			raw_item=raw_item.replace('<th ','<th style=\'border: 1px solid black\' ')
			raw_item=raw_item.replace('<td ','<td style=\'border: 1px solid black; height: 20px;\' ')
			return [pf.RawBlock(raw_item,'html')] 
	return None

#def beamer_notes(elem,doc):
#	if isinstance(elem,pf.Div) and "notes" in elem.classes:
#		if doc.format!="beamer":
#			return [] ##Remove notes for non beamer output
#		else:
#			left=pf.RawBlock('\\note{', format='latex')
#			right=pf.RawBlock('}', format='latex')
#			elem.content = [left] + list(elem.content) + [right]
#	return None


def filter_out_notes(elem,doc):
	if isinstance(elem,pf.Div) and "notes" in elem.classes and not (doc.format=="beamer" or doc.format=="revealjs" or doc.format=="slidy" or doc.format=="slideous"):
		return [] ##Remove notes for non beamer output

def exercise_filter(elem,doc):
	if isinstance(elem, pf.Para) and len(elem.content)==0:
		return [] ## Remove empty paragraphs ...
	elif isinstance(elem, pf.Header) and ("exercise" in elem.classes): # No need to use level 3 and elem.level==3:	
		if "reset" in elem.classes:
			doc.exercisecount=1
		else:
			doc.exercisecount+=1
		#print(sys.stderr,"Exercise detected",file=sys.stderr)
		doc.inside_exercise=True
		return []
	elif isinstance(elem, pf.Header) and ("question" in elem.classes): # No need to use level 3 and elem.level==3:	
		if "reset" in elem.classes:
			doc.questioncount=1
		else:
			doc.questioncount+=1
		#print(sys.stderr,"Exercise detected",file=sys.stderr)
		doc.inside_question=True
		return []
	elif doc.inside_exercise:
		if isinstance(elem, pf.Para)and len(elem.content)>0:
			cogollo=pf.Str(str(doc.exercisecount)+".-")
			elem.content = [pf.Strong(cogollo),pf.Space] + list(elem.content)
			doc.inside_exercise=False
			return elem
	elif doc.inside_question:
		if isinstance(elem, pf.Para) and len(elem.content)>0:
			cogollo=pf.Str(str(doc.questioncount)+".-")
			elem.content = [pf.Strong(cogollo),pf.Space] + list(elem.content)
			doc.inside_question=False
			return elem


def get_suitable_extension(extensions_format,doc_format):
	format_list=extensions_format.split(",")
	format_dict={}
	for item in format_list:
		tokens=item.split("/")
		format_dict[tokens[0]]=tokens[1]
		if doc_format==tokens[0]:
			return tokens[1]

	if "html" in format_dict and html_format(doc_format):
		return format_dict["html"]

	return ""

def figure_extensions(elem,doc):
	if isinstance(elem,pf.Image):
		url=elem.url
		## Skip regular URLS
		if '://' in url:
			return None			
		basename, file_extension = os.path.splitext(url)
		override_extension=False

		## Support for tikz 
		if file_extension==".tex" :
			if latex_format(doc.format):
				if "standalone" in elem.classes:
					if "standalone_opts" in elem.attributes:
						tag="includestandalone[%s]" % elem.attributes["standalone_opts"]
					else:
						tag="includestandalone"
				else:
					tag="input"	
				## tikz inline centered
				if len(elem.parent.content) == 3:
					return [pf.RawInline('\\'+tag+'{'+basename+'}',format='latex')]
				## Replace includegraphics with input (tikzpicture)
				raw_item=pf.convert_text(elem.parent, input_format='panflute', output_format='latex')
				#pf.debug(raw_item)
				replacement=r'\\'+tag+'{'+basename+'}'
				raw_item = re.sub(r'\\includegraphics\[*.*\]*\{.*\}',replacement, raw_item)
				#pf.debug(raw_item)
				return [pf.RawInline(raw_item,format='latex')]
			else:
				override_extension=True


		if (file_extension==".pdf" or file_extension==".eps") and html_format(doc.format):
			override_extension=True
		
		if file_extension=="":
			override_extension=True

		if override_extension:
			if "alt-ext" in elem.attributes:
				ext=get_suitable_extension(elem.attributes["alt-ext"],doc.format)
				if ext:
					elem.url=basename+ext

				del elem.attributes["alt-ext"]
			else:
				elem.url=basename



def alignment(elem,doc):
	if ((isinstance(elem,pf.Image) and len(elem.parent.content)>=2) or isinstance(elem,pf.Div)) and "align" in elem.attributes:
		align=elem.attributes["align"]
		is_span= (type(elem) == pf.Image)
		#pf.debug(type(elem.parent))
		#pf.debug(len(elem.parent.content))
		if latex_format(doc.format):
			del elem.attributes["align"]
			if align=="center":
				left = create_raw_item(is_span,'\\begin{center}\n', format='latex')
				right = create_raw_item(is_span,'\n\\end{center}', format='latex')
			elif align=="left":
				left = create_raw_item(is_span,'\\begin{flushleft}\n', format='latex')
				right = create_raw_item(is_span,'\n\\end{flushleft}', format='latex')
			elif align=="right":
				left = create_raw_item(is_span,'\\begin{flushright}\n', format='latex')
				right = create_raw_item(is_span,'\n\\end{flushright}', format='latex')
			else:
				return None		
			
			if is_span:
				del elem.parent.content[-1] ## Remove stupid trailing space 
				#elem.parent.content=[left,elem,right]
				elem.parent.content=[left,elem,right]
				return [left,elem,right]
			else:
				elem.content = [left] + list(elem.content) + [right]
		elif html_format(doc.format):
			if is_span:
				return None ## img already has align attribute and text-align does not
			else:
				if "style" in elem.attributes:
					elem.attributes["style"]+=";text-align:"+align
				else:
					elem.attributes["style"]="text-align:"+align



def beamer_transitions(elem,doc):
	if (type(elem) == pf.Span or type(elem) == pf.Div):

		if "only" in elem.attributes:
			keyword="only"
		elif "onslide" in elem.attributes:
			keyword="onslide"
		else:
			return 

		only=elem.attributes[keyword] 
		is_span=(type(elem) == pf.Span)
		del elem.attributes[keyword]

		if doc.format != 'beamer':
			return list(elem.content) ## return None

		left=create_raw_item(is_span,('\\%s<' % keyword)+only+'>{' , format='latex')
		right=create_raw_item(is_span,'}', format='latex')
		elem.content = [left] + list(elem.content) + [right]
		return None

			
def autounderlined(elem,doc):
	if doc.autounderlined and type(elem) == pf.Link:
		##Create a span with bogus content but class underline
		span=pf.Span(pf.Str('More'), pf.Space, pf.Str('words.'),classes=["underline"])
		## Force link's content to become the span's content
		span.content=elem.content
		## Put the span inside the link 
		elem.content=[span]
		#return the modified link
		return elem 

def advanced_blocks(elem,doc):
	if type(elem) == pf.Div and doc.format == 'beamer':
		## Retrieve title
		if "title" in elem.attributes:
			title="{"+elem.attributes["title"]+"}"
		else:
			title="{}"
			
		if 'block' in elem.classes:
			left = pf.RawBlock('\\begin{block}'+title, format='latex')
			right = pf.RawBlock('\\end{block}', format='latex')
			elem.content = [left] + list(elem.content) + [right]
		elif 'exampleblock' in elem.classes:
			left = pf.RawBlock('\\begin{exampleblock}'+title, format='latex')
			right = pf.RawBlock('\\end{exampleblock}', format='latex')
			elem.content = [left] + list(elem.content) + [right]
		elif 'alertblock' in elem.classes:
			left = pf.RawBlock('\\begin{alertblock}'+title, format='latex')
			right = pf.RawBlock('\\end{alertblock}', format='latex')
			elem.content = [left] + list(elem.content) + [right]
		elif 'whiteblock' in elem.classes:
			left = pf.RawBlock('\\begin{whiteblock}'+title, format='latex')
			right = pf.RawBlock('\\end{whiteblock}', format='latex')
			elem.content = [left] + list(elem.content) + [right]
		elif 'console' in elem.classes:
			left = pf.RawBlock('\\begin{console}'+title, format='latex')
			right = pf.RawBlock('\\end{console}', format='latex')
			elem.content = [left] + list(elem.content) + [right]
		return elem
	if type(elem) == pf.Header and "subsection" in elem.classes:
		if doc.format == 'beamer':
			return [pf.RawBlock('\\subsection{'+pf.stringify(elem)+'}', format='latex')]
		else:
			return []
	## General blocks		
	if type(elem) == pf.Div:
		if "shaded" in elem.classes:
			if latex_format(doc.format):
				left = pf.RawBlock('\\begin{shaded}', format='latex')
				right = pf.RawBlock('\\end{shaded}', format='latex')
				elem.content = [left] + list(elem.content) + [right]	
				return elem
			elif html_format(doc.format):
				token="background-color:#CCCCCC;"
				if "style" in elem.attributes:
					elem.attributes["style"]+=";"+token
				else:
					elem.attributes["style"]=token
				return elem
		if "framed" in elem.classes:
			if "height" in elem.attributes:
				height=Dimension(elem.attributes["height"])
			else:
				height=None
			
			if latex_format(doc.format):
				left=pf.RawBlock('\\begin{framed}', format='latex')
				right=pf.RawBlock('\\end{framed}', format='latex')
				elem.content=[left]+list(elem.content)+[right]
			elif html_format(doc.format):  
				if height==None:
					props="border: 1px solid black"
				else:
					props="border: 1px solid black;height:"+height.to_html()
				if "style" in elem.attributes:
					elem.attributes["style"]+=";"+props
				else:
					elem.attributes["style"]=props
			elif doc.format == "docx": ##
				if height==None:
					siz="2000"
				else:
					siz=height.width
				left=pf.RawBlock(r'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="8659" w:type="dxa"/></w:tblPr><w:tblGrid><w:gridCol w:w="8659"/></w:tblGrid><w:tr><w:trHeight w:val="'+siz+'" w:hRule="exact"/><w:tc><w:p>',format='openxml')
				right=pf.RawBlock(r'</w:p></w:tc></w:tr></w:tbl>',format='openxml')
				elem.content = [left] + list(elem.content) + [right]	
				return elem
	else:
		return


def add_pdfnotes(elem,doc):
	if doc.embed_pdfnotes and isinstance(elem,pf.Header) and elem.level==2:
		tag=r"\note{\includegraphics[page=%d,width=1.1\textwidth]{notes.pdf}}" % doc.note_counter
		doc.note_counter=doc.note_counter+1
		return [elem,pf.RawBlock(tag,"latex")]


def main(doc=None):
	#inputf = open('test.json', 'r')
	inputf=sys.stdin
	if doc is None:
		pf.debug("NONERRR")

	return pf.run_filters(actions=[lbegin_lend,exercise_filter,columns,pagebreaks,autounderlined,custom_span,filter_out_notes,custom_fontsize,alignment,advanced_blocks,beamer_transitions,table_separators,figure_extensions,add_pdfnotes], doc=doc,input_stream=inputf,prepare=prepare)

if __name__ == "__main__":
	main()