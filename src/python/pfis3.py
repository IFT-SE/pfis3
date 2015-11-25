import sys
import sqlite3
import networkx as nx
from nltk.stem import PorterStemmer
import iso8601
import bisect
import copy
import shutil
import os
import datetime
import getopt
import re

#imports for PFIS related classes
from navpath import *
from log import *
from java_processor import JavaHelper
from js_processor import JavaScriptHelper

# VOCAB:
# prevNavEntry = The navigation that we are predicting from
# currNavEntry = The navigation that the programmer actually went to
# In the context of prediction we use all the data that we have up to the
# timestamp of prevNavEntry to make a prediction. We compare that prediction
# against currNavEntry to get a rank


VERBOSE_BUILD = 0
VERBOSE_PATH = 0
VERBOSE_PREDICT = 1

HEADER_QUERY_1 = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' and timestamp < ? ORDER BY timestamp DESC"
HEADER_QUERY_2 = "INSERT INTO logger_log (user, timestamp, action, target, referrer, agent) VALUES (?, ?, ?, ?, ?, ?)"
SCENT_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN ('Package', 'Imports', 'Extends', 'Implements', 'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'Constructor invocation scent', 'Method declaration scent', 'Method invocation scent', 'New package', 'New file header') AND timestamp <= ?"
TOPOLOGY_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN ('Package', 'Imports', 'Extends', 'Implements', 'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'New package', 'Open call hierarchy') AND timestamp <= ?"
ADJACENCY_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' AND timestamp <= ? ORDER BY timestamp"
PATH_QUERY_1 = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Text selection offset' ORDER BY timestamp"
PATH_QUERY_2 = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' AND timestamp <= ? ORDER BY timestamp"
PATH_QUERY_3 = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration length' AND timestamp <= ? ORDER BY timestamp"

REGEX_SPLIT_CAMEL_CASE = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')


NUM_METHODS_KNOWN_ABOUT = 0
#remember that you have to multiply the number of iterations you want by 2
NUM_ITERATIONS = 2
DECAY_FACTOR = 0.85
PATH_DECAY_FACTOR = 0.9
INITIAL_ACTIVATION = 1

class Activation:
    def __init__(self, mapMethodsToScores):
        self.mapMethodsToScores = mapMethodsToScores

    def spread(self, graph):
    #Perform spreading activation computation on the graph by activating
    #nodes in the activation dictionary. activation = {} where key is node,
    #value is initial activation weight

        #i = the current node
        #j = iterated neighbor of i
        #x = iteration counter

        # if x is 0,2,4,6,... we want to spread out only to word nodes
        # if x is 1,3,5,7,... we want to spread out only to non-word nodes

        for x in range(NUM_ITERATIONS):
            for i in self.mapMethodsToScores.keys():
                if i not in graph:
                    continue
                w = 1.0 / len(graph.neighbors(i))
                for j in graph.neighbors(i):
                    if j not in self.mapMethodsToScores:
                        self.mapMethodsToScores[j] = 0.0
                    if (x % 2 == 0 and wordNode(j)) or (x % 2 != 0 and not wordNode(j)):
                        self.mapMethodsToScores[j] = self.mapMethodsToScores[j] + (self.mapMethodsToScores[i] * w * DECAY_FACTOR)
        return sorted(self.mapMethodsToScores.items(), sorter) # Returns a list of only nodes with weights

def loadLanguageSpecifics(language):
    #TODO: add a processor for JS
    if(language == "JAVA"):
        processor = JavaHelper()
    elif (language == "JS"):
        processor = JavaScriptHelper()
    return processor

def print_usage():
    print("python pfis3.py -d <dbPath> -s <stopwordsfile> -l <language> -p <project src folder path>")
    print("for language : say JAVA or JS")

def parseArgs():

    arguments = {
        "outputPath" : None,
        "stopWordsPath" : True,
        "tempDbPath" : None,
        "dbPath" : None,
        "projectSrcFolderPath": None,
        "language": None
    }

    def assign_argument_value(argsMap, option, value):
        optionKeyMap = {
            "-s" : "stopWordsPath",
            "-d" : "dbPath",
            "-l" : "language",
            "-p" : "projectSrcFolderPath"
        }

        key = optionKeyMap[option]
        arguments[key] = value

    def setConventionBasedArguments(argsMap):
        argsMap["tempDbPath"] = argsMap["dbPath"] + "_temp"
        argsMap["outputPath"] = argsMap["dbPath"] + "_out"

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "d:s:l:p:")
    except getopt.GetoptError as err:
        print str(err)
        print("Invalid args passed to PFIS")
        print_usage()
        sys.exit(2)
    for option, value in opts:
        assign_argument_value(arguments, option, value)

    #todo: currently, these are conventions, to avoid too many configurations. needs review.
    setConventionBasedArguments(arguments)

    return arguments


def main():

    args = parseArgs()

    # dbPath = '/Users/Dave/Desktop/code/pfis3/data/p8l_debug.db'
    # tempDbPath = '/Users/Dave/Desktop/p8l_debug_temp.db'
    # stopWordsPath = '/Users/Dave/Desktop/code/pfis3/data/je.txt'
    # ouputLogPath = '/Users/Dave/Desktop/pfis3_test.txt'
    # projectSrcFolderPath = '/Users/Dave/Desktop/p8l-vanillaMusic/src'
    # language = "JAVA"

    #Initialize the processor with the appropriate language specific processor
    processor = loadLanguageSpecifics(args["language"])

    # Start by making a working copy of the database
    copyDatabase(args["dbPath"], args["tempDbPath"])
    
    
    # The set of predictive algorithms to run
    predAlgs = [pfisWithHistory]
    
    
    paths = buildPath(args["tempDbPath"], processor.between_method, processor);
    stopWords = loadStopWords(args["stopWordsPath"])
    log = Log(args["outputPath"])
    predictAllNavigations(processor, paths, stopWords, log, args["tempDbPath"], args["projectSrcFolderPath"], predAlgs)

    sys.exit(0)

def predictAllNavigations(processor, navPathObj, stopWords, logObj, dbFile, \
                          projectSrcFolderPath, listPredictionAlgorithms):
    navNum = 0
    for entry in navPathObj:
        if entry.prevEntry:
            print "=================================================="
            if VERBOSE_PREDICT:
                print "Predicting navigation #"+ str(navNum)
                print "\tfrom:", entry.prevEntry.method
                print "\tto:", entry.method
            if entry.prevEntry.unknownMethod:
                headerFqn = addPFIGJavaFileHeader(processor, dbFile, entry,
                                                  projectSrcFolderPath, 
                                                  navPathObj)
                # Now the graph has the PFIG header nodes in it, but the navPath
                # has to be changed to reflect the new nodes that we added. We
                # have to check if headerFqn is not none, since it will return
                # None on navigations between two unknown methods
                if headerFqn:
                    entry.prevEntry.method = headerFqn
                    entry.prevEntry.unknownMethod = False
                
            # TODO: The graph does not need to be regenerated each time, it
            # would be sufficient to just add the new database row data from the
            # previous navigation's time stamp to the current navigation's time
            # stamp
            graph = buildGraph(processor, dbFile, stopWords, entry.timestamp)
            
            for predictAlg in listPredictionAlgorithms:
                    makePredictions(processor, navPathObj, navNum, graph, predictAlg,
                                    processor.between_method, resultsLog = logObj)
                    #logObj.saveLog()
            print "=================================================="

        navNum += 1


def loadStopWords(path):
    # Load the stop words from a file. The file is expected to have one stop
    # word per line. Stop words are ignored and not loaded into the PFIS graph.
    words = []
    f = open(path)
    for word in f:
        words.append(word.lower())
    return words

def addPFIGJavaFileHeader(processor, dbFile, navEntry, projectFolderPath, navPathObj):
    class PFIGFileHeader:
        def __init__(self, fqn, length, dt):
            self.fqn = fqn
            self.fqnClass = fqn[0:fqn.find(';') + 1]
            self.length = length
            ms = dt.microsecond / 1000
            self.timestamp = dt.strftime("%Y-%m-%d %H:%M:%S." + str(ms))
                
    def insertHeaderIntoDb(pfigHeader, classFilePath):
        print "Adding PFIG Header...", pfigHeader.fqn
        print "Reading file contents..."
        f = open(classFilePath, 'r')
        # TODO: Verify that contents is being handled by the predictive
        # algorithms correctly. They currently contain newlines, which the graph
        # producing code may be sensitive to.
        contents = f.read(pfigHeader.length)
        print "Done reading file contents."
        print "Adding header to database..."
        
        dummy = "auto-generated"
        timestamp = pfigHeader.timestamp
        
        c = conn.cursor()
        c.execute(HEADER_QUERY_2, [dummy, timestamp, 'Method declaration', pfigHeader.fqnClass, pfigHeader.fqn, dummy])
        c.execute(HEADER_QUERY_2, [dummy, timestamp, 'Method declaration offset', pfigHeader.fqn, str(0), dummy])
        c.execute(HEADER_QUERY_2, [dummy, timestamp, 'Method declaration length', pfigHeader.fqn, str(pfigHeader.length), dummy])
        c.execute(HEADER_QUERY_2, [dummy, timestamp, 'Method declaration scent', pfigHeader.fqn, contents, dummy])
        conn.commit()
        c.close()
        print "Done adding header to database."
        print "Done adding PFIG Header."
        
    
    _, className, _ = navEntry.prevEntry.method.split(",")
    ts = navEntry.timestamp

    classFilePath = os.path.join(projectFolderPath, className + processor.FileExtension)
    print classFilePath
    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    
    c = conn.cursor()
    c.execute(HEADER_QUERY_1, [ts])
    lowestOffset = -1
    fqn = None
    out = None
    
    for row in c:
        methodFqn, offset = row['target'], int(row['referrer'])
        
        # Get the class of the method    
        if className == processor.normalize(methodFqn):
            if lowestOffset == -1 or offset < lowestOffset:
                lowestOffset = offset
                fqn = methodFqn[0:methodFqn.rfind('.')]
                
    c.close()
    
    if lowestOffset > -1:
        fqn = fqn + '.pfigheader()V'
        dt = iso8601.parse_date(navEntry.prevEntry.timestamp)
        dt += datetime.timedelta(milliseconds=1)
        
        pfigHeader = PFIGFileHeader(fqn, lowestOffset, dt)
        insertHeaderIntoDb(pfigHeader, classFilePath)
        out = pfigHeader.fqn
    
    conn.close()
    return out
    
    
#==============================================================================#
# Methods to build the topology                                                #
#==============================================================================#

def buildGraph(processor, dbFile, stopWords, timestamp):
    global NUM_METHODS_KNOWN_ABOUT
    # Construct the undirected PFIS graph using the sqlite3 database found at
    # dbFile using the list of stop words contained in stopWords.
    graph = nx.Graph()
    NUM_METHODS_KNOWN_ABOUT = 0
    print "Building PFIS graph..."
    loadScentRelatedNodes(processor, graph, dbFile, stopWords, timestamp)
    loadTopologyRelatedNodes(processor, graph, dbFile, stopWords, timestamp)
    loadAdjacentMethods(processor, graph, dbFile, timestamp)
    print "Done building PFIS graph. Graph contains", NUM_METHODS_KNOWN_ABOUT, \
    "method nodes."

    return graph

def loadScentRelatedNodes(processor, graph, dbFile, stopWords, timestamp):
    # Attaches word nodes to the graph. Words nodes come from three types of
    # sources. These words are split according to camel case, or not and also
    # stemmed or not depending on the source of the word. The three cases are
    # described below. Some of the nodes here are then reused when the topology
    # is built in loadTopology.

    print "Processing scent. Adding word nodes to the graph..."

    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(SCENT_QUERY, [timestamp]);

    for row in c:
        action, target, referrer = \
            row['action'], processor.fixSlashes(row['target']), \
            processor.fixSlashes(row['referrer'])

        # Case 1: target and referrer contain either FQNs or file paths, so
        # create a  node for every target and referrer. Each of these nodes then
        # gets an edge to each of the words within the FQN or path, excluding
        # stop words. These words are not stemmed.
        if action in ('Package', 'Imports', 'Extends', 'Implements',
                      'Method declaration', 'Constructor invocation',
                      'Method invocation', 'Variable declaration',
                      'Variable type'):
            for word in getWordNodes_splitNoStem(target, stopWords):
                graph.add_edge(target, word)
                if VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]

            for word in getWordNodes_splitNoStem(referrer, stopWords):
                graph.add_edge(referrer, word)
                if VERBOSE_BUILD: print "\tAdding edge from", referrer, "to", word[1]

        # Case 2: For new packages, we want to connect the last part of the
        # package's name to the path containing the package (which should have
        # been added by the referrer of 'Package' in the step above).
        elif action in ('New package'):
            for word in getWordNodes_splitNoStem(target, stopWords):
                graph.add_edge(target, word)
                if VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]

        # Case 3: These actions have code content within them. In this case we
        # want to add an edge from the FQN node in target to the code content in
        # referrer. The FQNs should already exist because of step 1. Words are
        # added in two ways. In the first pass, the complete word is added,
        # camelCase intact without stemming. In the second pass, the camel case
        # is split, the resulting words are stemmed and those are added to the
        # FQN node.
        elif action in ('Constructor invocation scent',
                        'Method declaration scent', 'Method invocation scent',
                        'New file header'):
            for word in getWordNodes_splitNoStem(referrer, stopWords):
                graph.add_edge(target, word)
                if VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]

            for word in getWordNodes_splitCamelAndStem(referrer, stopWords):
                graph.add_edge(target, word)
                if VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]
    c.close()
    conn.close()
    print "Done processing scent."

def loadTopologyRelatedNodes(processor, graph, dbFile, stopWords, timestamp):
    # This method creates adds many edges to g according to the things logged by
    # PFIG. Specifically they are as follows:
    # 1. A node called "packages" to all packages (as a folder path)
    # 2. A node called "packages" to all project folder names in Eclipse
    # 3. All package folder paths to their project folder name
    # 4. All package folder paths to normalized class paths
    # 5. All FQNs to the normalized paths
    # 6. All normalized paths in target to normalized paths in referrer
    # 7. All targets to referrers for actions in TOPOLOGY_QUERY
    # This means that there are several nodes that create connections that are
    # not among those that are used to make predictions. Predictions only come
    # from methods nodes that are FQNs. Potentially this means, that if we
    # spread activation only once, many of these nodes have little effect on the
    # nodes that end up getting predicted. The only direct connection that
    # occurs between two methods that is relevant to prediction is when one
    # method calls another since that's the only way to link two FQNs that are
    # methods.

    print "Processing topology. Adding location nodes to the graph..."

    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(TOPOLOGY_QUERY, [timestamp])

    for row in c:
        action, target, referrer, = \
            row['action'], processor.fixSlashes(row['target']), \
            processor.fixSlashes(row['referrer'])

        ntarget = processor.normalize(target)
        nreferrer = processor.normalize(referrer)
        pack = processor.package(target)
        proj = processor.project(target)

        # Link the 'packages' node to new packages. Packages is a root node that
        # all the packages are connected to
        if action == 'New Package':
            graph.add_edge('packages', referrer)
        else:
            # Always connect target to referrer. Examples follow:
            # Package: /jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
            #           --> org/gjt/sp/jedit/gui
            # Imports: /jEdit/src/org/gjt/sp/jedit/bufferset/BufferSet.java
            #           --> Lorg/gjt/sp/util/Log;
            # Extends: Lorg/gjt/sp/jedit/View; --> Ljavax/swing/JFrame;
            # Implements: Lorg/gjt/sp/jedit/bufferset/BufferSet$PathSorter;
            #           --> Ljava/util/Comparator<Lorg/gjt/sp/jedit/Buffer;>;
            # Method declaration: Lorg/gjt/sp/jedit/bufferset/BufferSet;
            #           --> Lorg/gjt/sp/jedit/bufferset/BufferSet;.size()I
            # Constructor invocation: ?
            # Method invocation: Ljava/lang/String;.equals(Ljava/lang/Object;)Z
            #           --> scope.toString().equals(s)
            # Variable declaration:
            #           Lorg/gjt/sp/jedit/bufferset/BufferSet;.sort()V
            #           --> Lorg/gjt/sp/jedit/bufferset/BufferSet;
            #               .sort()V#listeners
            # Variable type:
            # Lorg/gjt/sp/jedit/bufferset/BufferSet;.moveBuffer(II)V#newPosition
            #           --> I
            # New package: /jEdit/src/org/gjt/sp/jedit ---> jEdit
            # Open call hierarchy: org/gjt/sp/jedit/gui/StatusBar
            #          --> Lorg/gjt/sp/jedit/gui/StatusBar;.updateCaretStatus()V
            graph.add_edge(target, referrer)
            if VERBOSE_BUILD: print "\tAdding edge from", target, "to", referrer

            # Connect the project name and the packages to the root packages
            # node
            if proj != '':
                graph.add_edge('packages', proj)
                if VERBOSE_BUILD: print "\tAdding edge from 'packages' to", proj

            if pack != '':
                graph.add_edge('packages', pack)
                if VERBOSE_BUILD: print "\tAdding edge from 'packages' to", pack

            # Attach packages to each class by their normalized path which
            # starts with the package name. See normalize().
            # Ex: org/gjt/sp/jedit --> org/gjt/sp/jedit/View
            if pack != '' and ntarget != '':
                graph.add_edge(pack, ntarget)
                if VERBOSE_BUILD:
                    print "\tAdding edge from", pack, "to", ntarget

            # Attach all package paths to the project node
            # Ex: jEdit --> org/gjt/sp/jedit/gui
            if pack != '' and proj != '':
                graph.add_edge(proj, pack)
                if VERBOSE_BUILD: print "\tAdding edge from", proj, "to", pack

            # Attaches normalized paths to FQNs See normalize().
            # Ex: org/gjt/sp/jedit/bufferset/BufferSet
            #       --> Lorg/gjt/sp/jedit/bufferset/BufferSet;.sort()V
            if ntarget != '':
                graph.add_edge(ntarget, target)
                if VERBOSE_BUILD:
                    print "\tAdding edge from", ntarget, "to", target

            # Attaches FQNs to normalized paths See normalize().
            # Ex: Lorg/gjt/sp/jedit/bufferset/BufferSet;.sort()V#listeners
            #       --> org/gjt/sp/jedit/bufferset/BufferSet
            if nreferrer != '':
                graph.add_edge(nreferrer, referrer)
                if VERBOSE_BUILD:
                    print "\tAdding edge from", nreferrer, "to", referrer

            # Attaches two FQNs normalized paths to each other. See normalize().
            # In most cases, this will be self-referential, but in the case of
            # Imports and Extends, this can link two different classes.
            # Ex: org/gjt/sp/jedit/bufferset/BufferSet
            #        --> org/gjt/sp/util/Log;
            if ntarget != '' and nreferrer != '':
                graph.add_edge(ntarget, nreferrer)
                if VERBOSE_BUILD:
                    print "\tAdding edge from", ntarget, "to", nreferrer
    c.close
    conn.close

    global NUM_METHODS_KNOWN_ABOUT

    for item in graph.nodes_iter():
        if item != '' and \
                      not wordNode(item) and \
                      '#' not in item and ';.' in item:
            NUM_METHODS_KNOWN_ABOUT += 1
    print "Done processing topology."

def loadAdjacentMethods(processor, graph, dbFile, timestamp):
    # Creates links between two methods that are adjacent in a class file. A
    # method is considered to be adjacent if it is the next method to be defined
    # in a class, even if there is stuff in between (like field declarations or
    # empty space.


    # A mapping of method offsets to method names per class
    # { class --> [ { "referrer" --> method offset, "target"
    #   --> method }, ... ] }
    offsets = {}

    #----------------------------------------------------------------------#
    # Inner methods for loadAdjacentMethods                                #
    #----------------------------------------------------------------------#
    def sorted_insert(l, item):
        # Insert the method declaration offset according to its position in the
        # class.
        # l: the dictionary of the class the method belongs to
        # item: contains the method offset and the method in the following
        #    format: { "referrer" --> method offset, "target" --> method }
        l.insert(bisect.bisect_left(l, item), item)

    def add_offset(timestamp, loc, target, referrer):
        # Add the method declaration offset to the offsets data structure.
        # This method will replace any existing occurrences with the new data
        # that is passed in.
        # timestamp: the datetime of the method declaration
        # loc: the class the method belongs as a normalized path
        # target: the FQN of the method to update
        # referrer: the character offset from the top of the file to the
        #   beginning of this method

        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = processor.getOuterClass(loc)
        if loc2 not in offsets:
            offsets[loc2] = []
        # Remove any existing occurrence of given target
        for item in offsets[loc2]:
            if item['target'] == target:
                offsets[loc2].remove(item)
        # Maintain an ordered list of method declaration offsets that is
        # always current as of this timestamp.
        sorted_insert(offsets[loc2],
                      {'referrer': referrer, 'target': target})

        # In each class, add an edge between two FQN methods if they are
        # adjacent in the same class.
        for i in range(len(offsets[loc2])):
            if i + 1 < len(offsets[loc2]):
                graph.add_edge(offsets[loc2][i]['target'],
                               offsets[loc2][i + 1]['target'])
                if VERBOSE_BUILD:
                    print "\tAdding edge from", offsets[loc2][i]['target'], \
                            "to", offsets[loc2][i + 1]['target']

    print "Processing adjacency. Adding adjacent methods to the graph..."

    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(ADJACENCY_QUERY, [timestamp])

    for row in c:
        timestamp, target, referrer = \
            iso8601.parse_date(row['timestamp']), row['target'], \
            int(row['referrer'])

        # Get the method's class
        loc = processor.normalize(target)
        if loc:
            add_offset(timestamp, loc, target, referrer)
    c.close()
    conn.close()
    print "Done processing adjacency."

#==============================================================================#
# Helper methods for building the graph                                        #
#==============================================================================#

def getWordNodes_splitNoStem(s, stopWords):
    # Returns a list of word nodes from the given string after stripping all
    # non-alphanumeric characters. A word node is a tuple containing 'word' and
    # a String containing the word. Words are always lower case. No stemming is
    # done in this case.
    return [('word', word.lower()) \
                for word in re.split(r'\W+|\s+', s) \
                if word != '' and word.lower() not in stopWords]

def getWordNodes_splitCamelAndStem(s, stopWords):
    # Returns a list of word nodes from the given string after stripping all
    # non-alphanumeric characters, splitting camel case and stemming each word.
    # A word node is a tuple that contains 'word' and a String containing the
    # word. Words are always lower case.
    return [('word', PorterStemmer().stem(word).lower()) \
                for word in splitCamelWords(s, stopWords) \
                if word.lower() not in stopWords]

def splitCamelWords(s, stopWords):
    # Split camel case words. E.g.,
    # camelSplit("HelloWorld.java {{RSSOwl_AtomFeedLoader}}")
    # --> ['Hello', 'World', 'java', 'RSS', 'Owl', 'Atom', 'Feed', 'Loader']
    result = []
    last = 0
    for match in REGEX_SPLIT_CAMEL_CASE.finditer(s):
        if s[last:match.start()] != '':
            result.append(s[last:match.start()])
        last = match.end()

    if s[last:] != '':
        result.append(s[last:])

    return result


#==============================================================================#
# Method for determining the path                                              #
#==============================================================================#
def buildPath(dbFile, granularityFunc, processor):
    # Reconstruct the original method-level path through the source code by
    # matching text selection offsets to method declaration offsets. Text
    # selection offsets occur later in the data than method declaration
    # offsets, so we can use this knowledge to speed up the reconstruction
    # query. It returns: A timestamped sequence of navigation among methods
    # (or classes if no method declaration offsets are available for that
    # class)

    # List of navigations as recorded by PFIG.
    # [ {"referrer" --> method offset, "loc" --> class }, ... ]
    nav = []

    # A mapping of method offsets to method names per class
    # { class --> [ { "offset" --> method start offset, "method"
    #   --> method, "end" --> method end offset }, ... ] }
    offsets = {}

    # Programmer path for output.
    out = NavPath()

    def sorted_insert(l, item):
        # Insert the method declaration offset according to its position in the
        # class.
        # l: the dictionary of the class the method belongs to
        # item: contains the method offset and the method in the following
        #    format: { "referrer" --> method offset, "target" --> method }
        l.insert(bisect.bisect_left(l, item), item)

    def add_nav(timestamp, loc, offset):
        # Add text selection navigation events to a structure.
        # timestamp = the timestamp of this text selection event
        # loc = the class that this text selection event occurred
        # offset = the number of characters from the top of the file the
        #   cursor start position was

        loc2 = processor.getOuterClass(loc)
        if loc2 not in offsets:
            offsets[loc2] = []

        nav.append({'timestamp': timestamp, 'offset': offset, 'loc': loc2})

    def add_start_offset(loc, method, offset):
        # Add the method declaration offset to the offsets data structure.
        # This method will replace any existing occurrences with the new data
        # that is passed in.
        # loc: the class the method belongs as a normalized path
        # method: the FQN of the method to update
        # offset: the character offset from the top of the file to the
        #   beginning of this method

        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = processor.getOuterClass(loc)
        if loc2 not in offsets:
            offsets[loc2] = []

        # Remove any existing occurrence of given target
        for item in offsets[loc2]:
            if item['method'] == target:
                offsets[loc2].remove(item)

        # Maintain an ordered list of method declaration offsets that is
        # always current as of this timestamp.
        sorted_insert(offsets[loc2],
                      {'offset': offset, 'method': method})

    def add_end_offset(loc, method, length):
        # Add the end character offset for passed in class's method. We don't
        # need to remove and reinsert, because we already did that in
        # add_start_offset()

        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = processor.getOuterClass(loc)

        for t in offsets[loc2]:
            if t['method'] == method:
                t['end'] = t['offset'] + length - 1

    def find_method_match(loc, offset):
        # Iterate over offsets and find the method that matches the passed in
        # class and offset
        # loc: The normalized class path to look up
        # offset: The number of characters from the top of the file to look up

        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 =  processor.getOuterClass(loc)
        if loc2 not in offsets:
            offsets[loc2] = []

        if loc2 in offsets:
            for t in offsets[loc2]:
                if offset >= t['offset'] and offset <= t['end']:
                    return t['method']

        return 'UNKNOWN,' + loc2 + ',' + str(offset)

    def clean_up_path():
        # Remove navigations to the same location and any navigations that are
        # between methods or after the last method. The only unknown location we
        # keep is are one that occur before the beginning of the first method as
        # those will become header navigations
        for i in reversed(range(out.getLength() - 1)):
            doDelete = False
            method1 = out.getMethodAt(i)
            method2 = out.getMethodAt(i + 1)
            method1IsUnknown = out.isUnknownMethodAt(i);
            method2IsUnknown = out.isUnknownMethodAt(i + 1);

            # Using the granularity function, remove any identical methods
            # Recall that granularity functions returns true when the two
            # passed-in parameters are true.
            if not granularityFunc(method1, method2):
                if VERBOSE_PATH:
                    print "\tRemoving duplicate method navigation at", str(i), \
                    method2
                doDelete = True

            # If the granularity is between method, we want to remove any
            # navigations that landed between method definitions and any methods
            # after the end of the file.

            #todo: make sure this "is between method?" comparison is not broken.
            if not doDelete and granularityFunc == processor.between_method:
                if method2IsUnknown:
                    tokens = method2.split(',')
                    loc = tokens[1]
                    offset = int(tokens[2])

                    # Remove any methods that are known to be in between two
                    # methods
                    if is_in_gap(loc, offset):
                        if VERBOSE_PATH:
                            print "\tRemoving navigation to gap between" \
                            +" methods at", str(i), method2
                        doDelete = True

                # Remove any duplicates that are in the same gap between methods
                # but at different offsets
                if not doDelete and method1IsUnknown \
                    and method2IsUnknown:
                    tokens1 = method1.split(',')
                    tokens2 = method2.split(',')
                    loc1 = tokens1[1]
                    loc2 = tokens2[1]

                    if loc1 == loc2:
                        offset1 = int(tokens1[2])
                        offset2 = int(tokens2[2])

                        if in_in_same_gap(loc1, offset1, offset2):
                            if VERBOSE_PATH:
                                print "\tRemoving duplicate navigation to gap" \
                                + " between methods at", str(i), method2
                            doDelete = True
            if doDelete:
                out.removeAt(i + 1)

    def is_in_gap(loc, offset):
        # Returns true if the given navigation is to a location between method
        # definitions or after the last method defintion for the given class
        # location and offset. Navigations to the top of a file, before the
        # start offset are not considered to be in a gap.

        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = processor.getOuterClass(loc)

        # If the class in offsets doesn't exist, it's a navigation to a new
        # file. If the location is before the first method, we keep it as it is
        # a header navigation
        if loc2 not in offsets or offset < offsets[loc2][0]['offset']:
            return False

        classOffsets = offsets[loc2]

        # Return true if the offset is past the last method.
        if offset > classOffsets[-1]['end']:
            return True

        # Return true if the offset is in between two methods
        if loc2 in offsets and len(classOffsets) > 1:
            for i in range(len(classOffsets) - 1):
                currMethod = classOffsets[i];
                nextMethod = classOffsets[i + 1]
                if offset > currMethod['end'] and offset < nextMethod['offset']:
                    return True

        return False

    def in_in_same_gap(loc, offset1, offset2):

        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = processor.getOuterClass(loc)

        # If the class in offsets doesn't exist, it's a navigation to a new
        # file. If the location is before the first method, we keep it as it is
        # a header navigation
        if loc2 not in offsets:
            return False

        classOffsets = offsets[loc2]

        # Return true if the offsets are past the last method.
        if offset > classOffsets[-1]['end'] \
            and offset2 > classOffsets[-1]['end']:
            return True

        # Return true if the offsets are in between the same two methods
        if loc2 in offsets and len(classOffsets) > 1:
            for i in range(len(classOffsets) - 1):
                currMethod = classOffsets[i];
                nextMethod = classOffsets[i + 1]
                if offset > currMethod['end'] \
                    and offset < nextMethod['offset'] \
                    and offset2 > currMethod['end'] \
                    and offset2 < nextMethod['offset']:
                    return True

        return False

    print "Building path..."

    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row

    # We need to combine data from method offsets and text cursor offsets

    # Store all the text selection offsets into the nav data structure
    c = conn.cursor()
    c.execute(PATH_QUERY_1)
    for row in c:
        timestamp, target, referrer = \
            (iso8601.parse_date(row['timestamp']), row['target'], \
            int(row['referrer']))

        # Get the class of the method
        loc = processor.normalize(target)
        if loc:
            add_nav(timestamp, loc, referrer)
    c.close()

    # The positions of the method declaration offsets could potentially change
    # between navigations. For example, text can be added or removed. To account
    # for this, each navigation must be handled independently with only the
    # data leading up to the navigation informing the offsets.

    for navData in nav:
        currentTime = navData["timestamp"]
        offset = navData["offset"]
        navLoc = navData["loc"]

        # Clear the offsets from the last iteration
        offsets.clear()

        # Fill the offsets data structure with all known method declaration
        # start positions.
        c = conn.cursor()
        c.execute(PATH_QUERY_2, [currentTime])
        for row in c:
            target, referrer = row['target'], int(row['referrer'])

            # Get the class of the method
            loc = processor.normalize(target)
            if loc:
                add_start_offset(loc, target, referrer)
        c.close()

        # Insert the end positions of all the methods in the offset data
        # structure
        c = conn.cursor()
        c.execute(PATH_QUERY_3, [currentTime])
        for row in c:
            target, referrer = row['target'], int(row['referrer'])

            # Get the class of the method
            loc = processor.normalize(target)
            if loc:
                add_end_offset(loc, target, referrer)
        c.close()

        # Lookup the offset in navs and get the method. Each element in navs
        # gets looked up and added to NavPath object as a NavPathEntry
        entry = NavPathEntry(currentTime, find_method_match(navLoc, offset))
        out.addEntry(entry)

        #out.append({'target': find_method_match(navLoc, offset),
        #    'timestamp': currentTime})
    conn.close()
    print "Cleaning up path according to specified granularity..."
    clean_up_path()

    if VERBOSE_PATH:
        print out.toStr()

    print "Done building path."
    return out


def makePredictions(processor, navPath, navNum, graph, algorithmFunc, granularityFunc, resultsLog,
                    bugReportWordList = []):
    # Iterate through the navigations with the selected granularityFunc and call
    # the algorithmFunc for each navigation to a new location (navigations are
    # specified by the granularityFunc). Results are stored in the resultsLog
    # data structure.
    #print "make Predictions called"
    entry = navPath.getEntryAt(navNum)
    if granularityFunc(entry.prevEntry.method, entry.method):
        algorithmFunc(processor, resultsLog, navPath, graph, entry.prevEntry, entry, \
                      navNum, bugReportWordList)

def pfisWithHistory(processor, resultsLog, navPath, graph, prevNavEntry, currNavEntry, i,
                    bugReportWordList):
    # One of the possible algorithm fucntions.
    # This version pre-weighs the participant's path with initial starting
    # weights before spreading activation. The current step is weighed with
    # INITIAL_ACTIVATION and every step in the past is decayed by the
    # PATH_DECAY_FACTOR.

    def getInitialPathWeights():
        # Weigh the navigation path prior to spreading activation. If the
        # programmer has been to the same location several times, the highest
        # weight is the one that is stored. Also, give an initial weight of 1
        # to all words that have been included in the bugReport

        a = INITIAL_ACTIVATION
        dictOfInitialWeights = {}
        # Set the dictOfInitialWeights of all bugReportWordList in
        # bugReportWordList to INITIAL_ACTIVATION
        for word in bugReportWordList:
            dictOfInitialWeights[word] = INITIAL_ACTIVATION

        # Iterate over resultsLog backwards. For each navigation with both start
        # and end nodes in the graph, apply a starting weight on those nodes
        # with a decay factor specified by PATH_DECAY_FACTOR
        for j in reversed(range(navPath.getLength())):
            #print j, navPath[j]['target'];
            jMethod = navPath.getMethodAt(j)
            if jMethod not in dictOfInitialWeights \
                or dictOfInitialWeights[jMethod] < a:
                dictOfInitialWeights[jMethod] = a
            a *= PATH_DECAY_FACTOR

        return dictOfInitialWeights

    ties = -1 # Added by me
    prevMethod = prevNavEntry.method
    currMethod = currNavEntry.method

    # There are two possibiliites when making a prediction
    # Possibility 1: Both the prevNavEntry (the one that we are predicting from)
    # and the currNavEntry (the location the programmer acually went) exits in 
    # the graph. If this is the case, then we weigh the nodes according to the 
    # path,  spread activation, and then get a ranked list of predictions.
    if prevMethod in graph and currMethod in graph:
        # Initially seed some of the weights
        dictOfInitialWeights = getInitialPathWeights()

        # Create an Activation object with those weights
        actObj = Activation(dictOfInitialWeights)

        # Spread activationa and get a list of all the nodes that have a
        # non-zero weight
        activation = actObj.spread(graph)

        rank, length, ties = \
            getResultRank(graph, currNavEntry.method, activation, navNum=i)
        if VERBOSE_PREDICT:
            print '\tLocation found. Rank =', rank

        e = LogEntry(i, rank, ties, length, prevMethod, currMethod,
                     processor.between_class(prevMethod, currMethod),
                     processor.between_package(prevMethod, currMethod),
                     currNavEntry.timestamp)
        resultsLog.addEntry(e);
    # Possibility 2, the method is unknown or somehow not in the graph, so we
    # mark it as such
    else:
        if VERBOSE_PREDICT:
            print '\tLocation not found.'
        e = LogEntry(i, 999999, ties, NUM_METHODS_KNOWN_ABOUT, prevMethod,
                     currMethod,
                     processor.between_class(prevMethod, currMethod),
                     processor.between_package(prevMethod, currMethod),
                     currNavEntry.timestamp)
        resultsLog.addEntry(e);

## CODE BELOW STILL NEEDS TO BE REFACTORED

def getResultRank(graph, currNav, activation, navNum=0):
    # sorts list of activations desc
    last = activation[0][0]
    #Here he removes everything but methods from activation
    scores = [val for (item,val) in activation if item != '' and \
                      item != last and not wordNode(item) and \
                      '#' not in item and ';.' in item]

    targets = [item for (item,val) in activation if item != '' and \
                      item != last and not wordNode(item) and \
                      '#' not in item and ';.' in item]
    #print "\ttargets vector has", len(targets), "nodes"
    rank = 0
    #found = 0
    for item in targets:
        rank += 1
        #print rank, item, val
        if item == currNav:
    #        #found = 1
            break
    #if found:
        #scores = []
    ranks = rankTransform(scores) # Returns a list of ranks that account for ties in reverse order
    rankTies = mapRankToTieCount(ranks)
    ties = rankTies[ranks[rank - 1]]
    #methods[agent][item] = (len(ranks) - ranks[i]) / (len(ranks) - 1)
    #writeScores(navNum, targets, ranks, scores) -- REMOVED BY ME
    #print "End:", currNav, "\trank:", rank, "\tranks[rank-1]:", ranks[rank - 1], "\tscores[rank-1]:", scores[rank-1]
    return (len(ranks) - ranks[rank - 1]), len(targets), ties
    #return (len(ranks) - ranks[rank - 1]) / (len(ranks) - 1), len(targets)
    #else:
    #    return 999998, len(targets)

def mapRankToTieCount(ranks):
# uses methods to create a mapping from the rank to the number of instances
# of that rank in the rank listing
# methods: { agent id --> { method --> rank }
# o: { rank --> number ties }

    o = {}
    for rank in ranks:
        if rank not in o:
            o[rank] = 1
        else:
            o[rank] = o[rank] + 1
    return o


#def writeScores(navnum, methods, ranks, scores):
# Writes the contents of methods to the specified file

#    for i in range(len(methods)):
#        activation_root.write("%d,%s,%s,%s\n" % (navnum, methods[i], (len(ranks) - ranks[i]), scores[i]))

#The following were pulled from the stats.py package
def rankTransform(scoresForMethods):
    #We need to add all the zero entries here
    extendedList = [0] * NUM_METHODS_KNOWN_ABOUT;
    for i in range(len(scoresForMethods)):
        extendedList[i] = scoresForMethods[i]

    # At this point, there's a sorted list of scores for every known method

    scoresVector, ranksVector = shellsort(extendedList)
    sumranks = 0
    dupcount = 0
    resultRankList = [0] * NUM_METHODS_KNOWN_ABOUT
    for i in range(NUM_METHODS_KNOWN_ABOUT):
        sumranks = sumranks + i
        dupcount = dupcount + 1
        if i==NUM_METHODS_KNOWN_ABOUT-1 or scoresVector[i] <> scoresVector[i+1]:
            averank = sumranks / float(dupcount) + 1
            for j in range(i-dupcount+1,i+1):
                resultRankList[ranksVector[j]] = averank
            sumranks = 0
            dupcount = 0
    return resultRankList

def shellsort(allScoresList):
    n = len(allScoresList)
    scoresVector = copy.deepcopy(allScoresList)
    ranksVector = range(n) # Int vector 0 to len n-1
    gap = n/2   # integer division needed
    while gap >0:
        for i in range(gap,n):
            for j in range(i-gap,-1,-gap):
                while j>=0 and scoresVector[j]>scoresVector[j+gap]:
                    temp        = scoresVector[j]
                    scoresVector[j]     = scoresVector[j+gap]
                    scoresVector[j+gap] = temp
                    itemp       = ranksVector[j]
                    ranksVector[j]     = ranksVector[j+gap]
                    ranksVector[j+gap] = itemp
        gap = gap / 2  # integer division needed
# scoresVector is now sorted allScoresList, and ranksVector has the order scoresVector[i] = vec[ranksVector[i]]
    return scoresVector, ranksVector

def sorter (x,y):
    return cmp(y[1],x[1])


def wordNode (n):
    return n[0] == 'word'

#==============================================================================#
# Build header file code
#==============================================================================#

def copyDatabase(dbpath, newdbpath):
    print "Making a working copy of the database..."
    shutil.copyfile(dbpath, newdbpath)
    print "Done."

if __name__ == "__main__":
    main()