# -*- Mode: Python; indent-tabs-mode: nil -*-

# Please adhere to the PEP 8 style guide:
#     http://www.python.org/dev/peps/pep-0008/

#Version: Naive models with rank transform

import sys
import sqlite3
import re
import bisect
import datetime
import iso8601
import copy
import os

# This regular expression captures forward and backward slashes
# It is used to convert Windows style slashes '\' to a single
# consistent UNIX style path with '/'
fix_regex = re.compile(r'[\\/]+')

def fix(string):
    return fix_regex.sub('/',string)

    
normalize_classfile = re.compile(r"(.*?);")
normalize_elim_subclass = re.compile(r"(.*?)\$")

def classfile(string):
# Return a proxy for the class file indicated in the string.
# If it can't be extracted, return the whole string

    m = normalize_classfile.match(string)
    if m: 
       m2 = normalize_elim_subclass.match(m.group(1))
       if m2:
           return m2.group(1)
       else:
           return m.group(1)
    else:
       return string


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
    
def loadNearbyMethods(nearby_methods):
# Loads known methods and offsets into a dictionary with the following
# format: { agent id --> { method --> offset } }

    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Method declaration offset')''')
    for row in c:
        user, action, target, referrer, agent = (row['user'][0:3],
                                                 row['action'],
                                                 fix(row['target']),
                                                 fix(row['referrer']),
                                                 row['agent'])
        if(agent not in nearby_methods):
            nearby_methods[agent] = {}
            
        nearby_methods[agent][target] = int(referrer)
    c.close()
    return nearby_methods

def loadDirectedCalledMethods(calledMethods = {}):
# Loads called methods from each methods and stores the in a structure
# with the following format:
# { agent id --> { method --> [ method called by method in key, ... ] } }

    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Constructor invocation', 'Method invocation')''')
    for row in c:
        user, action, target, referrer, agent = (row['user'][0:3],
                                                 row['action'],
                                                 fix(row['target']),
                                                 fix(row['referrer']),
                                                 row['agent'])
        if(agent not in calledMethods):
            calledMethods[agent] = {}
            
        if(target not in calledMethods[agent]):
            calledMethods[agent][target] = []
            
        if referrer not in calledMethods[agent][target]:
            calledMethods[agent][target].append(referrer)
    c.close()
    return calledMethods

def loadTwoWayCalledMethods(calledMethods = {}):
# Loads called methods from each methods and stores the in a structure
# with the following format:
# { agent id --> { method --> [ method called by method in key, ... ] } }

    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Constructor invocation', 'Method invocation', 'Open call link')''')
    for row in c:
        user, action, target, referrer, agent = (row['user'][0:3],
                                                 row['action'],
                                                 fix(row['target']),
                                                 fix(row['referrer']),
                                                 row['agent'])
        if(agent not in calledMethods):
            calledMethods[agent] = {}
            
        if(target not in calledMethods[agent]):
            calledMethods[agent][target] = []
            
        if(referrer not in calledMethods[agent]):
            calledMethods[agent][referrer] = []
            
        if referrer not in calledMethods[agent][target]:
            calledMethods[agent][target].append(referrer)
        if target not in calledMethods[agent][referrer]:
            calledMethods[agent][referrer].append(target)
    c.close()
    return calledMethods

def loadKnownMethods(methods = {}):
# Reads in the PFIG database and loads all the known methods into a dictionary
# with the following format: { agent id --> { method --> 0 } } where method denotes
# a fully qualified method header.  The use of a dictionary prevents duplicates

    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Method declaration','Constructor invocation', 'Method invocation')''')
    for row in c:
        user, action, target, referrer, agent = (row['user'][0:3],
                                                 row['action'],
                                                 fix(row['target']),
                                                 fix(row['referrer']),
                                                 row['agent'])
        if(agent not in methods):
            methods[agent] = {}
            
        methods[agent][target] = 0
        methods[agent][referrer] = 0
    c.close()
    return methods

    
def loadPaths():
# Reconstruct the original method-level path through the source code by
# matching text selection offsets to method declaration offsets. Text
# selection offsets occur later in the data than method declaration
# offsets, so we can use this knowledge to speed up the reconstruction
# query. It returns: A timestamped sequence of navigation among methods
# (or classes if no method declaration offsets are available for that
# class)

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
    
    # Add all known text cursor offsets to the dictionary: nav
    # Combine knowledge in nav and offsets to generate dictionary: out
    c = conn.cursor()
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
    c.close()
    # Significant changes end here
    
    # This may have to be uncommented, but I'm not sure yet
    #for agent in nav:
    #    if len(nav[agent]) > 0:
    #        get_out(agent, t)
    #        for item in nav[agent]:
    #            out[agent].append({'target': item['loc'], 'timestamp': t})
    return out  
    
def rankTransformHighBest(ranks, i):
    return (len(ranks) - ranks[i]) / (len(ranks) - 1)
  
def rankHighBest(ranks, i):
    return (len(ranks) - ranks[i])
  
def rankTransformLowBest(ranks, i):
    return (ranks[i] - 1) / (len(ranks) - 1)

def rankLowBest(ranks, i):
    return (ranks[i] - 1)
    
def scoreMethodsNaiveRecency(methods, paths):
# Scores path according to recency. More recent navigations are scored higher than
# older navigations. Places not visited receive no score. Results are then rank
# transformed, placed into the dict: methods and returned.
# ==== Variables =====
# methods: { agent id --> { method --> 0 } }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }

    def replaceScoresWithRanks(methods, ranks, agent):
    # Replaces the scores with the results of the rank transform
    # The rank transform results are the inverse of what we need meaning
    # that 0 is ranked as max and max is ranked at 0.  We have to invert
    # ===== Variables =====
    # methods: { agent id --> { method --> navigation number } }
    # ranks: [ rank transformed score for this index in methods, ... ]
    # agent: the current agent id
    
        i = 0
        
        # Replace scores with inverted (and now correct) ranks
        for item in methods[agent]:
            methods[agent][item] = rankHighBest(ranks, i)
            i += 1
        return methods

    # Step through all the navigation paths that we have and score
    # according to recency
    
    for agent in paths:
        i = 1
        for step in paths[agent]:
            if(step['target'] not in methods[agent]):
                methods[agent][step['target']] = 0
            else:
                # Score all but the current method
                if(i < len(paths[agent])):
                    methods[agent][step['target']] = i
            i += 1
        
        # Get scores for indicies in methods
        scores = [methods[agent][item] for item in methods[agent]]
        
        # Get ranks for those indicies
        ranks = rankTransform(scores);
        
        # Get the final mapping of methods to ranks for the current agent
        methods = replaceScoresWithRanks(methods, ranks, agent)  
        
    return methods
    
def scoreMethodsNaiveWorkingSet(methods, paths, delta):
#TODO Update comment
# Scores path according to working set. More recent navigations are scored higher than
# older navigations. Places not visited receive no score. Results are then rank
# transformed, placed into the dict: methods and returned.
# ==== Variables =====
# methods: { agent id --> { method --> 0 } }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }

    def replaceScoresWithRanks(methods, ranks, agent):
    # Replaces the scores with the results of the rank transform
    # The rank transform results are the inverse of what we need meaning
    # that 0 is ranked as max and max is ranked at 0.  We have to invert
    # ===== Variables =====
    # methods: { agent id --> { method --> navigation number } }
    # ranks: [ rank transformed score for this index in methods, ... ]
    # agent: the current agent id
    
        i = 0
        
        # Replace scores with inverted (and now correct) ranks
        for item in methods[agent]:
            methods[agent][item] = rankHighBest(ranks, i)
            i += 1
        return methods

    # Step through all the navigation paths that we have and score
    # according to recency
    
    # Delta included for working set discussion
    for agent in paths:
        i = 1
        for step in paths[agent]:
            #print "len =", len(paths[agent]), "i =", i
            if(step['target'] not in methods[agent]):
                methods[agent][step['target']] = 0
            else:
                # Score all but the current method
                if(i < len(paths[agent]) and i <= len(paths[agent]) and i > len(paths[agent]) - delta):
                    #print "len =", len(paths[agent]), "i =", i
                    methods[agent][step['target']] = 1
            i += 1
        
        # Get scores for indicies in methods
        scores = [methods[agent][item] for item in methods[agent]]
        
        # Get ranks for those indicies
        ranks = rankTransform(scores);
        
        # Get the final mapping of methods to ranks for the current agent
        methods = replaceScoresWithRanks(methods, ranks, agent)  
        
    return methods

def scoreMethodsNaiveFrequency(methods, paths):
# Scores path according to frequency. More frequently visited methods are scored higher than
# less visited methods. Places not visited receive no score. Results are then rank
# transformed, placed into the dict: methods and returned.
# ==== Variables =====
# methods: { agent id --> { method --> 0 } }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }

    def replaceScoresWithRanks(methods, ranks, agent):
    # Replaces the scores with the results of the rank transform
    # The rank transform results are the inverse of what we need meaning
    # that 0 is ranked as max and max is ranked at 0.  We have to invert
    # ===== Variables =====
    # methods: { agent id --> { method --> navigation number } }
    # ranks: [ rank transformed score for this index in methods, ... ]
    # agent: the current agent id
    
        i = 0
        
        # Replace scores with inverted (and now correct) ranks
        for item in methods[agent]:
            methods[agent][item] = rankHighBest(ranks, i)
            i += 1
        return methods

    # Step through all the navigation paths that we have and score
    # according to frequency
    for agent in paths:
        i = 1
        for step in paths[agent]:
            if(step['target'] not in methods[agent]):
                methods[agent][step['target']] = 0
            else:
                # Score all but the current method
                if(i < len(paths[agent])):
                    methods[agent][step['target']] = methods[agent][step['target']] + 1
            i += 1
        
        # Get scores for indicies in methods
        scores = [methods[agent][item] for item in methods[agent]]
        
        # Get ranks for those indicies
        ranks = rankTransform(scores);
        
        # Get the final mapping of methods to ranks for the current agent
        methods = replaceScoresWithRanks(methods, ranks, agent)  
        
    return methods

def scoreMethodsNaiveTfidf(methods, paths):
# Scores path according to tf-idf between bug text and source code. Results are then rank
# transformed, placed into the dict: methods and returned.  See runNaiveTfidfModel for
# important external dependencies.
# ==== Variables =====
# methods: { agent id --> { method --> 0 } }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }

    def replaceScoresWithRanks(methods, ranks, agent):
    # Replaces the scores with the results of the rank transform
    # The rank transform results are the inverse of what we need meaning
    # that 0 is ranked as max and max is ranked at 0.  We have to invert
    # ===== Variables =====
    # methods: { agent id --> { method --> navigation number } }
    # ranks: [ rank transformed score for this index in methods, ... ]
    # agent: the current agent id
    
        i = 0
        
        # Replace scores with inverted (and now correct) ranks
        for item in methods[agent]:
            methods[agent][item] = rankHighBest(ranks, i)
            i += 1
        return methods

    # Step through all the navigation paths that we have and score
    # according to tf-idf results
    for agent in paths:
        for step in paths[agent]:
            if(step['target'] not in methods[agent]):
                methods[agent][step['target']] = 0
        
        # Get scores for indicies in methods
        scores = [methods[agent][item] for item in methods[agent]]
        
        # Get ranks for those indicies
        ranks = rankTransform(scores);
        
        # Get the final mapping of methods to ranks for the current agent
        methods = replaceScoresWithRanks(methods, ranks, agent)  
        
    return methods
    
def scoreMethodsNaiveAdjacency(methods, paths, nearby_methods):
    
    def replaceScoresWithRanks(methods, ranks, agent):
        i = 0
        for item in methods[agent]:
            methods[agent][item] = rankHighBest(ranks, i)
            i += 1
        return methods
    
    for agent in paths:
        #for step in paths[agent]:
        step = paths[agent][len(paths[agent]) - 2]
        step_to_predict = paths[agent][len(paths[agent]) - 1]
        classname = classfile(step['target']) 
        
        #print "step =", step
        #print "step_to_predict =", step_to_predict
        #print "classname =", classname
        
        if (classname.startswith("Unknown node")):
            print "Adding..... ",step['target']
            methods[agent][step['target']] = 0   
        if (classfile(step_to_predict['target']).startswith("Unknown node")):
            print "Adding..... ",step_to_predict['target']
            methods[agent][step_to_predict['target']] = 0
            
        #print nearby_methods[agent]

        #lineno = nearby_methods[agent][step['target']]

        # Build a list of methods in the current class, along with their line numbers in the file
        methods_in_class = [] 
        for neigh in nearby_methods[agent]:
            if (classfile(neigh) == classname):
                methods_in_class.append([neigh, nearby_methods[agent][neigh]])
                
        #print "methods_in_class =", methods_in_class
    
        # sort the methods according to position in the file
        methods_in_class.sort(key = lambda k: k[1])
        posn = 1000

        # Assign sequential numbers to them (so that the difference in two numbers will
        # be the distance between two methods, measured in methods)
        for k in methods_in_class:
            nearby_methods[agent][k[0]] = posn
            if k[0] == step['target']:
                lineno = posn
            posn = posn + 1 

        # now assign a high number for methods in the same class, and subtract off the
        # number of methods away the target method is.  Methods that aren't in this
        # class remain ranked at 0, hence tied for last.
        for neigh in nearby_methods[agent]:
            if (classfile(neigh) == classname):
                methods[agent][neigh] = 200000-abs(nearby_methods[agent][neigh] - lineno)
          
        scores = [methods[agent][item] for item in methods[agent]]
        ranks = rankTransform(scores);
        methods = replaceScoresWithRanks(methods, ranks, agent)
        #printMethods(methods)
        
    return methods

def scoreMethodsNaiveCalledMethods(methods, paths, calledMethods, twoway=False):
 # Scores path according to ...
# ==== Variables =====
# methods: { agent id --> { method --> 0 } }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }
# calledMethods: { agent id --> { method --> [ method called by method in key, ... ] } }
 
    def replaceScoresWithRanks(methods, ranks, agent):
        i = 0
        for item in methods[agent]:
            methods[agent][item] = rankLowBest(ranks, i)
            i += 1
        return methods
    
    def scoreLinkedMethods(node, distance, agent):
        if agent in calledMethods and node in calledMethods[agent]:
            for neighbor in calledMethods[agent][node]:
                if methods[agent][neighbor] == 0 or methods[agent][neighbor] > distance:
                    methods[agent][neighbor] = distance
                    scoreLinkedMethods(neighbor, distance + 1, agent)
        
    
    for agent in paths:
        for step in paths[agent]:
            if(step['target'] not in methods[agent]):
                methods[agent][step['target']] = 0
                
        # Determine current method to predict from
        currentMethod = paths[agent][len(paths[agent]) - 2]["target"]
        
        if twoway:
            conn = sqlite3.connect(sourcefile)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Open call link')''')
            for row in c:
                user, action, target, referrer, agent = (row['user'][0:3],
                                                         row['action'],
                                                         fix(row['target']),
                                                         fix(row['referrer']),
                                                         row['agent'])
            
                if(target not in methods[agent]):
                    methods[agent][target] = 0
                    
                if(referrer not in methods[agent]):
                    methods[agent][referrer] = 0
            c.close()
    
        # Score the distance of all attached methods
        scoreLinkedMethods(currentMethod, 1, agent)
        
        # Score all methods with distance of 0 as max
        for item in methods[agent]:
            if methods[agent][item] == 0:
                methods[agent][item] = len(methods[agent])
        
        # Get scores for indicies in methods
        scores = [methods[agent][item] for item in methods[agent]]
        
        # Get ranks for those indicies
        ranks = rankTransform(scores);
        
        # Get the final mapping of methods to ranks for the current agent
        methods = replaceScoresWithRanks(methods, ranks, agent)
    return methods
    
def mapMethodsToRanks(path):
    # This is used for the naive tf-idf model.  It uses the output
    # from the jython tfidf.py file and uses it to map methods to
    # the tfidf scores.  Returns a 
    # dict: { agent id --> { method --> tfidf score } }
    
    rv = {}
    filelist = os.listdir(path)
    for agent in filelist:
        if os.path.isdir(path + agent):
            if not agent in rv:
                rv[agent] = {}
            ranks = open(path + agent + '/list.ranks', 'r')
            for line in ranks:
                agent, method, rank = line.rstrip('\n').split('\t')
                rv[agent][method] = rank
    return rv

def printMethods(methods):
# Debugging: printMethods prints contents of the variable methods
# ----- Variables -----
# methods: { agent id --> { method --> number or rank }

    for agent in methods:
        print "Agent:", agent
        for item in methods[agent]:
            print "\t", methods[agent][item], "=", item
            
def printCalledMethods(calledMethods):
# Debugging: printCalledMethods prints contents of the variable calledMethods
# ----- Variables -----
# calledMethods: { agent id --> { method --> [ method called by method in key, ... ] } }
    
    for agent in calledMethods:
        print "Agent:", agent
        for item in calledMethods[agent]:
            print "\t", item, "calls:"
            for calledItem in calledMethods[agent][item]:
                print "\t\t", calledItem
            
def writeResults(methods, paths, output):
# Outputs results to the file specified
# ----- Variables -----
# methods: { agent id --> { method --> rank }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }

    f = open(output, 'w')
    for agent in paths:
        step = paths[agent][len(paths[agent]) - 1]
        tieList = mapRankToTieCount(methods, agent)
        f.write("%s,%d,%s,%g,%g,%d,%s\n" % \
                    (agent,
                    len(paths[agent]) - 1,
                    step['timestamp'],
                    methods[agent][step['target']],
                    tieList[methods[agent][step['target']]],
                    len(methods[agent]),
                    step['target']))
    f.close()

def writeResultsTFIDFCurrent(methods, paths, output, methodCounts):
# Outputs results to the file specified
# ----- Variables -----
# methods: { agent id --> { method --> rank }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }

    f = open(output, 'w')
    for agent in paths:
        step = paths[agent][len(paths[agent]) - 1]
        tieList = mapRankToTieCount(methods, agent)
        f.write("%s,%d,%s,%g,%g,%d,%s\n" % \
                    (agent,
                    len(paths[agent]) - 1,
                    step['timestamp'],
                    methods[agent][step['target']],
                    tieList[methods[agent][step['target']]],
                    methodCounts[agent],
                    step['target']))
    f.close()
    
def writeScores(methods, filename="ranks.csv"):
# Writes the contents of methods to the specified file

    f = open(filename, 'w')
    for agent in methods:
        for method in methods[agent]:
            f.write("%s,%s\n" % (method, methods[agent][method]))
    f.close
    
def mapRankToTieCount(methods, agent):
# uses methods to create a mapping from the rank to the number of instances
# of that rank in the rank listing
# methods: { agent id --> { method --> rank }
# o: { rank --> number ties }
    
    o = {}
    
    for method in methods[agent]:
        rank = methods[agent][method]        
        if rank not in o:
            o[rank] = 1
        else:
            o[rank] = o[rank] + 1
                
    return o
            

#########################
#The following were pulled from the stats.py package
#########################
    
def rankTransform(inlist):
    n = len(inlist)
    svec, ivec = shellsort(inlist)
    sumranks = 0
    dupcount = 0
    newlist = [0]*n
    for i in range(n):
        sumranks = sumranks + i
        dupcount = dupcount + 1
        if i==n-1 or svec[i] <> svec[i+1]:
            averank = sumranks / float(dupcount) + 1
            for j in range(i-dupcount+1,i+1):
                newlist[ivec[j]] = averank
            sumranks = 0
            dupcount = 0
    return newlist

def shellsort(inlist):
    n = len(inlist)
    svec = copy.deepcopy(inlist)
    ivec = range(n)
    gap = n/2   # integer division needed
    while gap >0:
        for i in range(gap,n):
            for j in range(i-gap,-1,-gap):
                while j>=0 and svec[j]>svec[j+gap]:
                    temp        = svec[j]
                    svec[j]     = svec[j+gap]
                    svec[j+gap] = temp
                    itemp       = ivec[j]
                    ivec[j]     = ivec[j+gap]
                    ivec[j+gap] = itemp
        gap = gap / 2  # integer division needed
# svec is now sorted inlist, and ivec has the order svec[i] = vec[ivec[i]]
    return svec, ivec

#########################
###End stats.py code
#########################

def runNaiveRecencyModel(sourcefile, outputDir):
    paths = loadPaths()
    methods = loadKnownMethods({})
    methods = scoreMethodsNaiveRecency(methods, paths)
    writeScores(methods, outputDir + "ranksRecency.csv")
    writeResults(methods, paths, outputDir + "naiveRecency.csv")
    
def runNaiveWorkingSetModel(sourcefile, outputDir):
    for i in range(3, 21):
        paths = loadPaths()
        methods = loadKnownMethods({})
        methods = scoreMethodsNaiveWorkingSet(methods, paths, i)
        writeScores(methods, outputDir + "ranksWorkingSet" + str(i) + ".csv")
        writeResults(methods, paths, outputDir + "naiveWorkingSet" + str(i) + ".csv")
    
def runNaiveFrequencyModel(sourcefile, outputDir):
    paths = loadPaths()
    methods = loadKnownMethods({})
    methods = scoreMethodsNaiveFrequency(methods, paths)
    writeScores(methods, outputDir + "ranksFrequency.csv")
    writeResults(methods, paths, outputDir + "naiveFrequency.csv")
    
def runNaiveTfidfModel(sourcefile, outputDir):
    # Note that you have to run the following first:
    #  1. python createDocs.py
    #  This reads in the PFIG database and creates a TF-IDF document for
    #  each method.  These are stored as text files in a directory.  These
    #  files are then used by step 2
    #  2. jython tfidf.py
    #  This uses the output from step 1 and the Java library created by
    #  Chris Scaffidi to generate output files that score the documents
    #  against the bug tests.
    #
    # You can view more details in the other files.
    # Only after 1 and 2 can you run the following
    
    paths = loadPaths()
    methodToRank = mapMethodsToRanks(sys.argv[2])
    methods = scoreMethodsNaiveTfidf(methodToRank, paths)
    writeScores(methods, outputDir + "ranksTfidf.csv")
    writeResults(methods, paths, outputDir + "naiveTfidf.csv")

def runNaiveTfidfCurrentMethodModel(sourcefile, outputDir):
    # Note that you have to run the following first:
    #  1. python createDocs.py
    #  This reads in the PFIG database and creates a TF-IDF document for
    #  each method.  These are stored as text files in a directory.  These
    #  files are then used by step 2
    #  2. jython tfidf.py
    #  This uses the output from step 1 and the Java library created by
    #  Chris Scaffidi to generate output files that score the documents
    #  against the bug tests.
    #
    # You can view more details in the other files.
    # Only after 1 and 2 can you run the following
    
    paths = loadPaths()
    methodToRank = mapMethodsToRanks(sys.argv[2])
    methods = scoreMethodsNaiveTfidf(methodToRank, paths)
    writeScores(methods, outputDir + "ranksTfidfCurrentMethod.csv")
    methodCounts = countTxtFiles(sys.argv[2])
    writeResultsTFIDFCurrent(methods, paths, outputDir + "naiveTfidfCurrentMethod.csv", methodCounts)

def countTxtFiles(dir):
    rv = {}

    if dir[-1] != '/':
        dir += '/'

    for path in os.listdir(dir):
        if os.path.isdir(dir + path):
            rv[path] = len(os.listdir(dir + path)) - 1;

    return rv
    
def runNaiveAdjacencyModel(sourcefile, outputDir):
    paths = loadPaths()
    methods = loadKnownMethods({})
    nearby_methods = loadNearbyMethods({})
    methods = scoreMethodsNaiveAdjacency(methods, paths, nearby_methods)
    writeScores(methods, outputDir + "ranksAdjacency.csv")
    writeResults(methods, paths, outputDir + "naiveAdjacency.csv")

def runNaiveCalledMethodModel(sourcefile, outputDir):
    paths = loadPaths()
    methods = loadKnownMethods({})
    calledMethods = loadTwoWayCalledMethods({})
    methods = scoreMethodsNaiveCalledMethods(methods, paths, calledMethods, twoway=True)
    writeScores(methods, outputDir + "ranksCalledMethod.csv")
    writeResults(methods, paths, outputDir + "naiveCalledMethod.csv")
    
def runNaiveDirectedCalledMethodModel(sourcefile, outputDir):
    paths = loadPaths()
    methods = loadKnownMethods({})
    calledMethods = loadDirectedCalledMethods({})
    methods = scoreMethodsNaiveCalledMethods(methods, paths, calledMethods)
    writeScores(methods, outputDir + "ranksDirectedCalledMethod.csv")
    writeResults(methods, paths, outputDir + "naiveDirectedCalledMethod.csv")
    
def main():
    global sourcefile

    if len(sys.argv) == 4:
        sourcefile = sys.argv[1]
        
        if sys.argv[2][-1] != '/':
            sys.argv[2] += '/'
        if sys.argv[3][-1] != '/':
            sys.argv[3] += '/'
            
        outputDir = sys.argv[3]
        
        #paths = loadPaths()
        #print "Path length =", len(paths['a23fe51d-196a-45b3-addf-3db4e8423e4f'])
        
        #print "\tRunning naive recency model..."    
        #runNaiveRecencyModel(sourcefile, outputDir)
        #print "\tRunning naive working set model..."    
        #runNaiveWorkingSetModel(sourcefile, outputDir)
        #print "\tRunning naive frequency model..."
        #runNaiveFrequencyModel(sourcefile, outputDir)
        #print "\tRunning naive TF-IDF model..."
        #runNaiveTfidfModel(sourcefile, outputDir)
        #print "\tRunning naive adjacency model..."
        #runNaiveAdjacencyModel(sourcefile, outputDir)
        #print "\tRunning naive called method model..."
        #runNaiveCalledMethodModel(sourcefile, outputDir)
        #print "\tRunning naive directed called method model..."
        #runNaiveDirectedCalledMethodModel(sourcefile, outputDir)
        print "\tRunning naive TF-IDF current method model..."
        runNaiveTfidfCurrentMethodModel(sourcefile, outputDir)
    else:
        print "\tUsage: python pfis2-participantK.py <PFIG database> <directory of documents from createDocs.py> <output directory>"
        
    sys.exit(0)

if __name__ == "__main__":
    main()
