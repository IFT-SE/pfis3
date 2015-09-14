#!/usr/bin/env jython
import sys
import sqlite3
import os
import shutil
import re
import bisect
import datetime
import iso8601

# This regular expression captures forward and backward slashes
# It is used to convert Windows style slashes '\' to a single
# consistent UNIX style path with '/'
fix_regex = re.compile(r'[\\/]+')

def fix(string):
    return fix_regex.sub('/',string)

# Returns the class path of a fully qualified class or method declaration
normalize_eclipse = re.compile(r"L([^;]+);.*")
# Returns the class path of a file path to a java file
normalize_path = re.compile(r".*src\/(.*)\.java")

def normalize(string):
# Return the class indicated in the string.
# File-name example:
# Raw file name: jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
# Normalized file name: org/gjt/sp/jedit/gui/StatusBar

    m = normalize_eclipse.match(string)
    if m:
        return m.group(1)
    n = normalize_path.match(fix(string))
    if n:
        return n.group(1)
    return ''

def makeDocumentFilesForNavs(sourcefile, outfile, methodToFile):
# Creates a directory of files for TF-IDF.  The root directory passed
# in is where the files are created.  Each file created contains the
# contents of a method as it was stored by the PFIG database.  Duplicates
# are handled by overwriting older method entries with newer ones.
# Also creates an index file, index.idx in the root directory that maps
# file paths to method names
# ===== Variables =====
# sourcefile = path to PFIG database
# outfile = path to where to create the current nav

    # List of navigations as recorded by PFIG.
    # { agent id --> [ { "timestamp" --> timestamp, "referrer" --> method offset, "loc" --> class }, ... ] }
    nav = {}

    # Programmer path for output.  The list is sorted by time.
    # { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }
    out = {}

    # A mapping of method offsets to method names per class
    # { agent id --> { class --> [ { "referrer" --> method offset, "target" --> method }, ... ] } }
    offsets = {}

    def sorted_insert(l, item):
    # Inserts items into a list in ascending order
        l.insert(bisect.bisect_left(l, item), item)

    def add_nav(agent, timestamp, loc, referrer):
    # Add text selection navigation events to a structure. 
    # 20 seconds is added to each nav to work around a race condition in PFIG
        
        timestamp += datetime.timedelta(seconds=20)
        if agent not in nav:
            nav[agent] = []
            
        nav[agent].append({'timestamp': timestamp,
                           'referrer': referrer,
                           'loc': loc})

    def add_offset(agent, timestamp, loc, target, referrer):
    # Update method declaration offset in offsets data structure. More
    # recent entries for a method declaration offset in PFIG replace
    # older versions in our topology.  This accounts for any text changes
    # in the code and allows all the offset calculations to remain correct
    # ===== Variables =====
    # loc = the class
    # target = the method
    # referrer = the offset of the method
        
        # This split allows inner classes to be handled properly
        loc2 = loc.split('$')[0]
        if agent not in offsets:
            offsets[agent] = {}
        if loc2 not in offsets[agent]:
            offsets[agent][loc2] = []
            
        # Remove any existing occurrence of given target
        for item in offsets[agent][loc2]:
            if item['target'] == target:
                offsets[agent][loc2].remove(item)
                
        # Maintain an ordered list of method declaration offsets that is
        # always current as of this timestamp.
        sorted_insert(offsets[agent][loc2],
                      {'referrer': referrer, 'target': target})

    def get_out(agent, timestamp):
        # Match text selection navigation data to the method declaration
        # offset data to determine the method being visited.  If method does
        # not exist in the topology, it is recorded as an unknown node in
        # the known class
        
        if agent not in out:
            out[agent] = []
        # This was replaced since we no longer have the guarantee of knowing all
        # the methods and contents that a programmer will visit in the future.
        # The timestamp condition had to be removed as a result
        # Original While Loop:           
        #        while agent in nav and agent in offsets and \
        #                len(nav[agent]) > 0 and \
        #                timestamp >= nav[agent][0]['timestamp']:

        # Modified While Loop:
        while agent in nav and agent in offsets and \
                len(nav[agent]) > 0:
            referrer = nav[agent][0]['referrer']
            loc = nav[agent][0]['loc']
            curts = nav[agent][0]['timestamp']
            
            # If method declaration offsets are unavailable ie., the method 
            # does not exist in the topology, append to out
            # without the method name
            if loc not in offsets[agent]:
                out[agent].append({'target': "Unknown node in: " + loc,
                                   'timestamp': curts})
                nav[agent].pop(0)
                continue
            
            # Otherwise, lookup the method declaration offset for this
            # navigation event. 'zz' is the max string.  It's a hack, 
            # but it works.  Here we get the index to insert into our list
            # of outs
            index = bisect.bisect_left(offsets[agent][loc],
                                       {'referrer': referrer,
                                        'target': 'zz'}) - 1
            if index < 0:
                index = 0
            out[agent].append({'target': offsets[agent][loc][index]['target'],
                               'timestamp': curts})
            nav[agent].pop(0)

    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Significant change here where we need to distinguish between method offsets and text offsets 
    # Add all the known methods positions to the dictionary: offsets
    c.execute("select timestamp,action,target,referrer,agent from logger_log where action in ('Method declaration offset') order by timestamp")
    t = None
    for row in c:
        timestamp, action, agent, target, referrer = \
            (iso8601.parse_date(row['timestamp']),
             row['action'],
             row['agent'],
             row['target'],
             int(row['referrer']))
        loc = normalize(target)
        if loc:
            add_offset(agent, timestamp, loc, target, referrer)
            t = timestamp
    c.close()

    javaMethod = ''
    currentAgent = ''

    # Add all known text cursor offsets to the dictionary: nav
    # Combine knowledge in nav and offsets to generate dictionary: out
    # Do it only once, for the most recent nav
    c.execute("select timestamp,action,target,referrer,agent from logger_log where action in ('Text selection offset') order by timestamp")
    for row in c:
        timestamp, action, agent, target, referrer = \
            (iso8601.parse_date(row['timestamp']),
             row['action'],
             row['agent'],
             row['target'],
             int(row['referrer']))
        loc = normalize(target)
        if loc:
            add_nav(agent, timestamp, loc, referrer)
            get_out(agent, timestamp)

        javaMethod = out[agent][len(out[agent]) - 2]["target"]
        currentAgent = agent
    c.close()
    # Significant changes end here

    #Taking the lazy approach
    file = shutil.copy(methodToFile[currentAgent][javaMethod], outfile)
        
    # Replace unicode newlines with ascii newlines
    #file.write(referrer.replace('/u000a', '\n'))
    #file.close

def readIndex(docsPath, file):
    rv = {}

    if docsPath[-1] != '/':
        docsPath += '/'

    idx = open(docsPath + file, 'r')
    for line in idx:
        filepath, method = line.rstrip('\n').split('\t')
        agent, filename = filepath.split('/')
        if not agent in rv:
            rv[agent] = {}
        rv[agent][method] = docsPath + agent + '/' + filename
    return rv

def main():
    if len(sys.argv) == 4:
        methodToFile = readIndex(sys.argv[3], "index.idx")
    	makeDocumentFilesForNavs(sys.argv[1], sys.argv[2], methodToFile)
    else:
    	print "\tUsage: python createNavFiles.py <PFIG database> <output file> <docs dir>"
    	
    sys.exit(0)


if __name__ == "__main__":
    main()
