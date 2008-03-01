#!/usr/bin/env python

# voter.py - vote reader for Super Tuesday

import csv
import os
import re
import time
import urllib
import states
#from template import *

import private
from candidates import candidates
#import reader


import simplejson as sj
import random

#def str( text ):
#	strings = {
#		'county': 'town',
#		'counties': 'towns'
#	}
#	return strings[text] or text

def getLeader( county, party ):
	tally = county.get(party)
	if tally == None  or  len(tally) == 0:
		return None
	return reader.candidates['byname'][party][ tally[0]['name'] ]

def partyName( party ):
	return { 'democrat':'Democratic', 'republican':'Republican' }[ party ]

def formatNumber( number ):
	return str(number)

def json( obj ):
	#return sj.dumps( obj, indent=4 )
	return sj.dumps( obj, separators=( ',', ':' ) )


parties = {
	'dem': { 'name':'Democrats' },
	'gop': { 'name':'Republicans' }
}

def fetchData():
	urllib.urlretrieve( private.csvFeedUrl, 'text_output_for_mapping.csv' )
	pass

		## Correct error in census data for Wentworth's Location
		#if( name == "Wentworth" and number == '9' ):
		#	name = "Wentworth's Location"

def readVotes():
	print 'Processing vote data'
	#reader = csv.reader( open( 'test.csv', 'rb' ) )
	reader = csv.reader( open( 'text_output_for_mapping.csv', 'rb' ) )
	header = []
	while header == []:
		header = reader.next()
	#print header
	for row in reader:
		if len(row) < 2: continue
		print row[0], row[1]
		setData( header, row )

def setData( header, row ):
	entity = state = states.byAbbr[ row[0] ]
	if 'counties' not in state: state['counties'] = {}
	setVotes( state, header, row )

def getPrecincts( row ):
	return {
		'reporting': int(row[3]),
		'total': int(row[2])
	}

def setVotes( entity, header, row ):
	counties = entity['counties']
	countyname = row[1]
	if countyname != '*':
		if countyname not in counties:
			counties[countyname] = { 'parties':{ 'dem':{}, 'gop':{} } }
		entity = counties[countyname]
	for col in xrange( 4, len(header) ):
		if col >= len(row) or row[col] == '': continue
		name = header[col]
		candidate = candidates['byname'][name]
		party = candidate['party']
		p = entity['parties'][party]
		if 'precincts' not in p: p['precincts'] = getPrecincts( row )
		if 'votes' not in p: p['votes'] = {}
		p['votes'][name] = int(row[col])

def percentage( n ):
	pct = int( round( 100.0 * float(n) ) )
	if pct == 100 and n < 1: pct = 99
	return pct

def sortVotes( party ):
	tally = []
	for name, votes in party['votes'].iteritems():
		tally.append({ 'name':name, 'votes':votes })
	tally.sort( lambda a, b: b['votes'] - a['votes'] )
	party['votes'] = tally

def makeJson( party ):
	ustotal = 0
	usvotes = {}
	usprecincts = { 'total': 0, 'reporting': 0 }
	usparty = { 'votes': usvotes, 'precincts': usprecincts }
	statevotes = {}
	for state in states.array:
		statetotal = 0
		parties = state['parties']
		if party not in parties: continue
		stateparty = state['parties'][party]
		stateparty['name'] = state['name']
		if 'votes' not in stateparty: continue
		sortVotes( stateparty )
		statevotes[ state['abbr'] ] = stateparty
		for vote in stateparty['votes']:
			name = vote['name']
			count = vote['votes']
			if name not in usvotes:
				usvotes[name] = 0
			usvotes[name] += count
			ustotal += count
			statetotal += count
		countyvotes = {}
		counties = state['counties']
		for countyname, county in counties.iteritems():
			countyparty = county['parties'][party]
			countyparty['name'] = countyname
			sortVotes( countyparty )
			countytotal = 0
			for vote in countyparty['votes']:
				countytotal += vote['votes']
			countyparty['total'] = countytotal
			countyvotes[countyname] = countyparty
		write(
			'votes/%s_%s.js' %( state['abbr'].lower(), party ),
			'Json.results(%s)' % json({
					'status': 'ok',
					'party': party,
					'state': state['abbr'],
					'total': statetotal,
					'totals': stateparty,
					'locals': countyvotes
			}) )
	sortVotes( usparty )
	write(
		'votes/%s_%s.js' %( 'us', party ),
		'Json.%sResults(%s)' %( party, json({
				'status': 'ok',
				'party': party,
				'state': 'us',
				'total': ustotal,
				'totals': usparty,
				'locals': statevotes
		}) ) )
		
	#state = data['state']
	#counties = data['counties']
	#for county in counties.itervalues():
	#	#del county['centroid']
	#	del county['shapes']
	#
	#result = {
	#	'status': 'ok',
	#	'state': state,
	#	'counties': counties
	#}
	#
	#write(
	#	'results_%s.js' % party,
	#	'Json.%sResults(%s)' %( party, json(result) )
	#)
	#
	#print '%s of %s precincts reporting' %( state['precincts']['reporting'], state['precincts']['total'] )

def write( name, text ):
	#print 'Writing ' + name
	f = open( name, 'w' )
	f.write( text )
	f.close()
	
def update():
	#print 'Retrieving data...'
	#fetchData()
	print 'Parsing data...'
	readVotes()
	print 'Creating Maps JSON...'
	makeJson( 'dem' )
	makeJson( 'gop' )
	#print 'Checking in Maps JSON...'
	#os.system( 'svn ci -m "Vote update" sc_text_output_for_mapping.csv data.js results_democrat.js results_republican.js' )
	print 'Done!'

def main():
	#while 1:
		update()
		#print 'Waiting 10 minute...'
		#time.sleep( 600 )

if __name__ == "__main__":
    main()
