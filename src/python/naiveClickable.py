# -*- Mode: Python; indent-tabs-mode: nil -*-

# Please adhere to the PEP 8 style guide:
#     http://www.python.org/dev/peps/pep-0008/

#Version: by navigation, 2 steps per iteration

import sys
from math import log
import sqlite3
import networkx as nx
import re
import bisect
import datetime
import iso8601
from nltk.stem import PorterStemmer
import cPickle
import copy

stop = {}
sourcefile = ''
activation_root = ''
topolen = 0
#remember that you have to multiply the number of iterations you want by 2
numIterations = 2


def stopwords():
    dp_numStopWords = 0
    f = open(sys.argv[2])
    for line in f:
        stop[line[0:-1]] = 1
        dp_numStopWords += 1
        


if len(stop) == 0:
    stopwords()

camelSplitter = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')


def camelSplit(string):
    '''Split camel case words. E.g.,

    >>> camelSplit("HelloWorld.java {{RSSOwl_AtomFeedLoader}}")
    ['Hello', 'World', 'java', 'RSS', 'Owl', 'Atom', 'Feed', 'Loader']
    '''
    result = []
    last = 0
    for match in camelSplitter.finditer(string):
        if string[last:match.start()] != '':
            result.append(string[last:match.start()])
        last = match.end()
    if string[last:] != '':
        result.append(string[last:])
    return result


def indexCamelWords(string):
    return [('word',
             PorterStemmer().stem(word).lower()) for word in \
                camelSplit(string) if word.lower() not in stop]


def indexWords(string):
    return [('word',
             word.lower()) for word in re.split(r'\W+|\s+',string) \
                if word != '' and word.lower() not in stop]


fix_regex = re.compile(r'[\\/]+')


def fix(string):
    return fix_regex.sub('/',string)


normalize_eclipse = re.compile(r"L([^;]+);.*")
normalize_path = re.compile(r".*src\/(.*)\.java")


def normalize(string):
    '''
    Return the class indicated in the string.
    File-name example:
    Raw file name: jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
    Normalized file name: org/gjt/sp/jedit/gui/StatusBar

    '''
    m = normalize_eclipse.match(string)
    if m:
        return m.group(1)
    n = normalize_path.match(fix(string))
    if n:
        return n.group(1)
    return ''


package_regex = re.compile(r"(.*)/[a-zA-Z0-9]+")


def package(string):
    '''Return the package.'''
    m = package_regex.match(normalize(string))
    if m:
        return m.group(1)
    return ''


project_regex = re.compile(r"\/(.*)\/src/.*")


def project(string):
    '''Return the project.'''
    m = project_regex.match(fix(string))
    if m:
        return m.group(1)
    return ''


# Package (type -> package)
# Imports (type -> type)
# Extends (type -> type)
# Implements (type -> type)
# Method declaration (type -> method)
# Constructor invocation (method -> method)
# Method invocation (method -> method)
# Variable declaration (type -> variable)
# Variable type (variable -> type)


# TODO: This function is currently dead code; it may be broken
#def checkTopology(g):
#    '''For which graphs are there disconnects?'''
#    for key in g:
#        if not nx.is_connected(g[key]):
#            print key


# TODO: This function is currently dead code; it may be broken
#def graphDiameters(graphs):
#    '''What's the radius and diameter of each graph?'''
#    for key in graphs:
#        if len(graphs[key]) < 2000:
#            if len(nx.connected_component_subgraphs(graphs[key])) > 1:
#                for g in nx.connected_component_subgraphs(graphs[key]):
#                    print key, len(g), nx.radius(g), nx.diameter(g)
#            continue
#        print key, len(graphs[key]), nx.radius(graphs[key]), \
#            nx.diameter(graphs[key])


def loadScents(graphs={}):
    '''Load just the scent portion of the graphs'''
    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Package','Imports','Extends','Implements','Method declaration','Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'Constructor invocation scent', 'Method declaration scent', 'Method invocation scent')''')
    for row in c:
        user, action, target, referrer, agent = (row['user'][0:3],
                                                 row['action'],
                                                 fix(row['target']),
                                                 fix(row['referrer']),
                                                 row['agent'])
        if agent not in graphs:
            graphs[agent] = nx.Graph()
        if action in ('Package', 'Imports', 'Extends', 'Implements',
                      'Method declaration', 'Constructor invocation',
                      'Method invocation', 'Variable declaration',
                      'Variable type'):
            
            # Connect class to constituent words
            for word in indexWords(target):
                graphs[agent].add_edge(target, word)
            # Connect import to constituent words
            for word in indexWords(referrer):
                graphs[agent].add_edge(referrer, word)
        elif action in ('Constructor invocation scent',
                        'Method declaration scent',
                        'Method invocation scent'):
            for word in indexWords(referrer):
                graphs[agent].add_edge(target,word)
            for word in indexCamelWords(referrer):
                graphs[agent].add_edge(target,word)
    c.close()
    
    return graphs


def loadTopology(graphs={}):
    '''Load just the topology portion of the graphs'''
    lastAgent = ''
    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Package','Imports','Extends','Implements','Method declaration','Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'Open call link')''')
    for row in c:
        user, action, target, referrer, agent = (row['user'][0:3],
                                                 row['action'],
                                                 fix(row['target']),
                                                 fix(row['referrer']),
                                                 row['agent'])
        if agent not in graphs:
            graphs[agent] = nx.Graph()
        # Connect topology
        ntarget = normalize(target)
        nreferrer = normalize(referrer)
        pack = package(target)
        proj = project(target)
        if proj != '':
            graphs[agent].add_edge('packages', proj)
        if pack != '':
            graphs[agent].add_edge('packages', pack)
        if pack != '' and ntarget != '':
            graphs[agent].add_edge(pack, ntarget)
        if pack != '' and proj != '':
            graphs[agent].add_edge(proj, pack)
        graphs[agent].add_edge(target, referrer)
        if ntarget != '':
            graphs[agent].add_edge(ntarget, target)
        if nreferrer != '':
            graphs[agent].add_edge(nreferrer, referrer)
        if ntarget != '' and nreferrer != '':
            graphs[agent].add_edge(ntarget, nreferrer)
        lastAgent = agent
    c.close()
    
    global topolen
    
    for item in graphs[agent].nodes_iter():
        if item != '' and \
                      not wordNode(item) and \
                      '#' not in item and ';.' in item:
            topolen += 1
    
    #print graphs[lastAgent].neighbors('Lorg/gjt/sp/jedit/ServiceManager;.getService(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;')
    return graphs


def loadScrolls(graphs={}):
    '''Load the scroll (adjacency) information from the db'''
    offsets = {}

    def sorted_insert(l, item):
        l.insert(bisect.bisect_left(l, item), item)

    def add_offset(agent, timestamp, loc, target, referrer):
        '''Update method declaration offset in offsets data structure'''
        if agent not in offsets:
            offsets[agent] = {}
        if loc not in offsets[agent]:
            offsets[agent][loc] = []
        if agent not in graphs:
            graphs[agent] = nx.Graph()
        # Remove any existing occurrence of given target
        for item in offsets[agent][loc]:
            if item['target'] == target:
                offsets[agent][loc].remove(item)
        # Maintain an ordered list of method declaration offsets that is
        # always current as of this timestamp.
        sorted_insert(offsets[agent][loc],
                      {'referrer': referrer, 'target': target})
        for i in range(len(offsets[agent][loc])):
            if i+1 < len(offsets[agent][loc]):
                graphs[agent].add_edge(offsets[agent][loc][i]['target'],
                                       offsets[agent][loc][i+1]['target'])

    
    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("select timestamp,action,target,referrer,agent from logger_log where action in ('Method declaration offset') order by timestamp")

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
    c.close()
    return graphs

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
    c = conn.cursor()
    
    # Add all known text cursor offsets to the dictionary: nav
    # Combine knowledge in nav and offsets to generate dictionary: out
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

def loadKnownMethods(methods = {}):
# Reads in the PFIG database and loads all the known methods into a dictionary
# with the following format: { agent id --> { method --> 0 } } where method denotes
# a fully qualified method header.  The use of a dictionary prevents duplicates

    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Method declaration','Constructor invocation', 'Method invocation', 'Open call link')''')
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


def init():
    global topolen
    topolen = 0
    g = {}
    #print '\tLoading scent data...'
    #g = loadScents(g)
    print '\tLoading topology data...'
    g = loadTopology(g)
    print '\tLoading scroll data...'
    g = loadScrolls(g)
    return g



def wordNode (n):
    return n[0] == 'word'

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

def scoreMethodsNaiveClickable(methods, paths, g):
 # Scores path according to ...
# ==== Variables =====
# methods: { agent id --> { method --> 0 } }
# paths: { agent id --> [ { "target" --> method, "timestamp" --> timestamp }, ... ] }
# g: the graph
 
    def replaceScoresWithRanks(methods, ranks, agent):
        i = 0
        for item in methods[agent]:
            methods[agent][item] = ranks[i] - 1
            i += 1
        return methods
    
    def scoreLinkedMethods(agent):
        for item in methods[agent]:
            if not item.startswith("Unknown node") and not currentMethod.startswith("Unknown node"):
                try:
                    methods[agent][item] = nx.shortest_path_length(g[agent], currentMethod, item)
                except nx.exception.NetworkXNoPath:
                    methods[agent][item] = 999999
                    
    for agent in paths:
        for step in paths[agent]:
            if(step['target'] not in methods[agent]):
                methods[agent][step['target']] = 0
                
        # Determine current method to predict from
        currentMethod = paths[agent][len(paths[agent]) - 2]["target"]
        nextMethod = paths[agent][len(paths[agent]) - 1]
    
        # Score the distance of all attached methods
        scoreLinkedMethods(agent)
        
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

def prepareAllNodes(g):
    rv = {}
    for agent in g:
        if not agent in rv:
            rv[agent] = {}
        for item in g[agent].nodes():
            rv[agent][item] = 0
    return rv

def runNaiveClickableModel(sourcefile, outputDir):
    g = init()
    paths = loadPaths()
    methods = loadKnownMethods({})
    methods = scoreMethodsNaiveClickable(methods, paths, g)
    writeScores(methods, outputDir + "ranksClicakable.csv")
    writeResults(methods, paths, outputDir + "naiveClickable.csv")

def main():
    global sourcefile
    if len(sys.argv) == 4:
        sourcefile = sys.argv[1]
        
        if sys.argv[3][-1] != '/':
            sys.argv[3] += '/'
            
        outputDir = sys.argv[3]
        
        print "\tRunning naive clickable model..."
        runNaiveClickableModel(sourcefile, outputDir)
    else:
        print "\tUsage: python naiveClickable.py <PFIG database> <stop words file> <output directory>"
        
    sys.exit(0)

if __name__ == "__main__":
    main()

sys.exit(0)
