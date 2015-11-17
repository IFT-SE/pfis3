import sys
import sqlite3
import re
import networkx as nx
from nltk.stem import PorterStemmer
import iso8601
import bisect


VERBOSE = 1

SCENT_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN ('Package', 'Imports', 'Extends', 'Implements', 'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'Constructor invocation scent', 'Method declaration scent', 'Method invocation scent', 'New package', 'New file header')"

TOPOLOGY_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN ('Package', 'Imports', 'Extends', 'Implements', 'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'New package', 'Open call hierarchy')"

ADJACENCY_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' ORDER BY timestamp"

PATH_QUERY_1 = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Text selection offset' ORDER BY timestamp"

PATH_QUERY_2 = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' AND timestamp <= ? ORDER BY timestamp"

PATH_QUERY_3 = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration length' AND timestamp <= ? ORDER BY timestamp"



REGEX_FIX_SLASHES = re.compile(r'[\\/]+')
REGEX_SPLIT_CAMEL_CASE = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')
REGEX_NORM_ECLIPSE = re.compile(r"L([^;]+);.*")
REGEX_NORM_PATH = re.compile(r".*src\/(.*)\.java")
REGEX_PROJECT = re.compile(r"\/(.*)\/src/.*")
REGEX_PACKAGE = re.compile(r"(.*)/[a-zA-Z0-9]+")



def main():
    stopWords = loadStopWords('/Users/Dave/Desktop/pfis3/data/je.txt')
    #g = buildGraph('/Users/Dave/Desktop/pfis3/data/sqlite.db', stopWords)
    p = buildPath('/Users/Dave/Desktop/pfis3/data/sqlite_fixed.db');


    sys.exit(0);
    
def loadStopWords(path):
    # Load the stop words from a file. The file is expected to have one stop 
    # word per line. Stop words are ignored and not loaded into the PFIS graph.
    words = []
    f = open(path)
    
    for word in f:
        words.append(word.lower())
        
    return words
    
#==============================================================================#
# Methods to build the topology                                                #
#==============================================================================#

def buildGraph(dbFile, stopWords):
    # Construct the undirected PFIS graph using the sqlite3 database found at 
    # dbFile using the list of stop words contained in stopWords.
    g = nx.Graph()
    loadScentRelatedNodes(g, dbFile, stopWords)
    loadTopologyRelatedNodes(g, dbFile, stopWords)
    loadAdjacentMethods(g, dbFile)
    
    return g
    
def loadScentRelatedNodes(g, dbFile, stopWords):
    # Attaches word nodes to the graph. Words nodes come from three types of
    # sources. These words are split according to camel case, or not and also
    # stemmed or not depending on the source of the word. The three cases are
    # described below. Some of the nodes here are then reused when the topology
    # is built in loadTopology.
    
    if VERBOSE: print "Processing scent. Adding word nodes to the graph..."
    
    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(SCENT_QUERY);
    
    for row in c:
        action, target, referrer, agent = \
            row['action'], fixSlashes(row['target']), \
            fixSlashes(row['referrer'])
        
        # Case 1: target and referrer contain either FQNs or file paths, so 
        # create a  node for every target and referrer. Each of these nodes then 
        # gets an edge to each of the words within the FQN or path, excluding 
        # stop words. These words are not stemmed.
        if action in ('Package', 'Imports', 'Extends', 'Implements',
                      'Method declaration', 'Constructor invocation',
                      'Method invocation', 'Variable declaration',
                      'Variable type'):
            for word in getWordNodes_splitNoStem(target, stopWords):
                g.add_edge(target, word)
                if VERBOSE: print "\tAdding edge from", target, "to", word[1]
            
            for word in getWordNodes_splitNoStem(referrer, stopWords):
                g.add_edge(referrer, word)
                if VERBOSE: print "\tAdding edge from", referrer, "to", word[1]
                     
        # Case 2: For new packages, we want to connect the last part of the 
        # package's name to the path containing the package (which should have 
        # been added by the referrer of 'Package' in the step above).
        elif action in ('New package'):
            for word in getWordNodes_splitNoStem(target, stopWords):
                g.add_edge(target, word)
                if VERBOSE: print "\tAdding edge from", target, "to", word[1]
                
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
                g.add_edge(target, word)
                if VERBOSE: print "\tAdding edge from", target, "to", word[1]
        
            for word in getWordNodes_splitCamelAndStem(referrer, stopWords):
                g.add_edge(target, word)
                if VERBOSE: print "\tAdding edge from", target, "to", word[1]
    c.close() 
    
    if VERBOSE: print "Done processing scent."
    
def loadTopologyRelatedNodes(g, dbFile, stopWords):
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
    
    if VERBOSE: 
        print "Processing topology. Adding location nodes to the graph..."
    
    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(TOPOLOGY_QUERY)
        
    for row in c:
        action, target, referrer, agent = \
            row['action'], fixSlashes(row['target']), \
            fixSlashes(row['referrer'])
            
        ntarget = normalize(target)
        nreferrer = normalize(referrer)
        pack = package(target)
        proj = project(target)
        
        # Link the 'packages' node to new packages. Packages is a root node that
        # all the packages are connected to
        if action == 'New Package':
            g.add_edge('packages', referrer)
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
            g.add_edge(target, referrer)
            if VERBOSE: print "\tAdding edge from", target, "to", referrer
        
            # Connect the project name and the packages to the root packages
            # node
            if proj != '':
                g.add_edge('packages', proj)
                if VERBOSE: print "\tAdding edge from 'packages' to", proj
                
            if pack != '':
                g.add_edge('packages', pack)
                if VERBOSE: print "\tAdding edge from 'packages' to", pack
                
            # Attach packages to each class by their normalized path which 
            # starts with the package name. See normalize().
            # Ex: org/gjt/sp/jedit --> org/gjt/sp/jedit/View
            if pack != '' and ntarget != '':
                g.add_edge(pack, ntarget)
                if VERBOSE: print "\tAdding edge from", pack, "to", ntarget
                
            # Attach all package paths to the project node
            # Ex: jEdit --> org/gjt/sp/jedit/gui
            if pack != '' and proj != '':
                g.add_edge(proj, pack)
                if VERBOSE: print "\tAdding edge from", proj, "to", pack
                
            # Attaches normalized paths to FQNs See normalize().
            # Ex: org/gjt/sp/jedit/bufferset/BufferSet 
            #       --> Lorg/gjt/sp/jedit/bufferset/BufferSet;.sort()V
            if ntarget != '':
                g.add_edge(ntarget, target)
                if VERBOSE: print "\tAdding edge from", ntarget, "to", target
                
            # Attaches FQNs to normalized paths See normalize().
            # Ex: Lorg/gjt/sp/jedit/bufferset/BufferSet;.sort()V#listeners
            #       --> org/gjt/sp/jedit/bufferset/BufferSet
            if nreferrer != '':
                g.add_edge(nreferrer, referrer)
                if VERBOSE:
                    print "\tAdding edge from", nreferrer, "to", referrer
            
            # Attaches two FQNs normalized paths to each other. See normalize().
            # In most cases, this will be self-referential, but in the case of
            # Imports and Extends, this can link two different classes.
            # Ex: org/gjt/sp/jedit/bufferset/BufferSet
            #        --> org/gjt/sp/util/Log;
            if ntarget != '' and nreferrer != '':
                g.add_edge(ntarget, nreferrer)
                if VERBOSE: print "\tAdding edge from", ntarget, "to", nreferrer
    c.close
    
    if VERBOSE: print "Done processing topology."
    
def loadAdjacentMethods(g, dbFile):
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
        loc2 = loc.split('$')[0]
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
                g.add_edge(offsets[loc2][i]['target'],
                                offsets[loc2][i + 1]['target'])
                if VERBOSE: 
                    print "\tAdding edge from", offsets[loc2][i]['target'], \
                            "to", offsets[loc2][i + 1]['target']
                            
    if VERBOSE: 
        print "Processing adjacency. Adding adjacent methods to the graph..."
    
    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(ADJACENCY_QUERY)

    for row in c:
        timestamp, action, target, referrer = \
            iso8601.parse_date(row['timestamp']), row['action'], \
            row['target'], int(row['referrer'])
        
        # Get the method's class
        loc = normalize(target)
        if loc:
            add_offset(timestamp, loc, target, referrer)
    c.close()
    
#==============================================================================#
# Helper methods for building the graph                                        #
#==============================================================================#
    
def fixSlashes(s):
    # Replaces '\' with '/'
    return REGEX_FIX_SLASHES.sub('/', s)
    
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
    
def normalize(s):
    # Return the class indicated in the string. Empty string returned on fail.
    # File-name example:
    # Raw file name: jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
    # Normalized file name: org/gjt/sp/jedit/gui/StatusBar

    m = REGEX_NORM_ECLIPSE.match(s)
    if m:
        return m.group(1)
    n = REGEX_NORM_PATH.match(fixSlashes(s))
    if n:
        return n.group(1)
    return ''

def package(s):
    # Return the package. Empty string returned on fail.
    # Ex: Lorg/gjt/sp/jedit/gui/statusbar/LineSepWidgetFactory$LineSepWidget -->
    #     org/gjt/sp/jedit/gui/statusbar
    m = REGEX_PACKAGE.match(normalize(s))
    if m:
        return m.group(1)
    return ''

def project(s):
    # Return the root folder in the given path. Empty string returned on fail. 
    # In Eclipse, the root folder would be the project folder.
    # Ex: /jEdit/src/org/gjt/sp/jedit/search --> jEdit
    m = REGEX_PROJECT.match(fixSlashes(s))
    if m:
        return m.group(1)
    return ''
    
#==============================================================================#
# Method for determining the path                                              #
#==============================================================================#
def buildPath(dbFile):
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
    
    # Programmer path for output.  The list is sorted by time.
    # [ { "target" --> method, "timestamp" --> timestamp }, ... ]
    out = []

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
    
        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = loc.split('$')[0]
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
        loc2 = loc.split('$')[0]
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
        loc2 = loc.split('$')[0]
        
        for tuple in offsets[loc2]:
            if tuple['method'] == method:
                tuple['end'] = tuple['offset'] + length - 1
                
    def find_method_match(loc, offset):
        # Iterate over offsets and find the method that matches the passed in
        # class and offset
        # loc: The normalized class path to look up
        # offset: The number of characters from the top of the file to look up
    
        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = loc.split('$')[0]
        if loc2 not in offsets:
            offsets[loc2] = []
        
        if loc2 not in offsets:
            print "Unknown location:", loc2;
        else:
            for tuple in offsets[loc2]:
                if offset >= tuple['offset'] and offset <= tuple['end']:
                    return tuple['method']
                    
        return 'Unknown location'

    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    
    # We need to combine data from method offsets and text cursor offsets
        
    # Store all the text selection offsets into the nav data structure
    c = conn.cursor()
    c.execute(PATH_QUERY_1)
    for row in c:
        timestamp, action, target, referrer = \
            (iso8601.parse_date(row['timestamp']), row['action'], \
            row['target'], int(row['referrer']))
        
        # Get the class of the method    
        loc = normalize(target)
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
            action, target, referrer = \
                row['action'], row['target'], int(row['referrer'])
            
            # Get the class of the method
            loc = normalize(target)
            if loc:
                add_start_offset(loc, target, referrer)
        c.close()
    
        # Insert the end positions of all the methods in the offset data 
        # structure
        c = conn.cursor()
        c.execute(PATH_QUERY_3, [currentTime])
        for row in c:
            action, target, referrer = \
                row['action'], row['target'], int(row['referrer'])
            
            # Get the class of the method
            loc = normalize(target)
            if loc:
                add_end_offset(loc, target, referrer)
        c.close()
        
        # Lookup the offset in navs and get the method. Each element in navs
        # gets looked up and added to the out structure, which represents the
        # participant's path
        out.append({'target': find_method_match(navLoc, offset), 
            'timestamp': currentTime})
    return out
    
    
    
    
if __name__ == "__main__":
    main()