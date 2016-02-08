import networkx as nx
import re
import sqlite3
from navpath import NavigationPath
from nltk.stem import PorterStemmer

class PfisGraph(object):
    
    #NAVIGATION_TIMESTAMPS_QUERY = "SELECT timestamp, action, target, referrer from logger_log WHERE action = 'Text selection offset' ORDER BY timestamp"
    
    
    SCENT_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN " \
                  "('Package', 'Imports', 'Extends', 'Implements', " \
                  "'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', " \
                  "'Constructor invocation scent', 'Method declaration scent', 'Method invocation scent', " \
                  "'New package', 'New file header') " \
                  "AND timestamp >= ? AND timestamp < ?"
    TOPOLOGY_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN " \
                     "('Package', 'Imports', 'Extends', 'Implements', " \
                     "'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', " \
                     "'New package', 'Open call hierarchy') " \
                     "AND timestamp >= ? AND timestamp < ?"
    ADJACENCY_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' " \
                      "AND timestamp >= ? AND timestamp < ? ORDER BY timestamp"
                      
    REGEX_SPLIT_CAMEL_CASE = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')
    

    def __init__(self, dbFilePath, langHelper, projSrc, stopWords = [], verbose=False):
        self.dbFilePath = dbFilePath
        self.langHelper = langHelper
        self.stopWords = stopWords
        self.VERBOSE_BUILD = verbose
        self.graph = None
        self.methods = None
        self.endTimestamp = '0'
        self.navPath = NavigationPath(dbFilePath, langHelper, projSrc)
        self.__initGraph()
    
    def __initGraph(self):
        conn = sqlite3.connect(self.dbFilePath)
        conn.row_factory = sqlite3.Row
        self.graph = nx.Graph()
        self.methods = []
        
        newEndTimestamp = 0
        if len(self.navPath.navigations) > 0:
            newEndTimestamp = self.navPath.navigations[0].toFileNav.timestamp
            
        
        self.__addScentNodesUpTo(conn, newEndTimestamp)
        #self.__addTopologyNodes(conn)
        #self.__addAdjacencyNodes(conn)
        conn.close()
        
        
    
    def __addScentNodesUpTo(self, conn, newEndTimestamp):
        c = conn.cursor()
        num = c.execute(self.SCENT_QUERY, [self.endTimestamp, newEndTimestamp])
        
        for row in c:
            action, target, referrer = \
                row['action'], self.langHelper.fixSlashes(row['target']), \
                self.langHelper.fixSlashes(row['referrer'])
        
            # Case 1: target and referrer contain either FQNs or file paths, so
            # create a  node for every target and referrer. Each of these nodes then
            # gets an edge to each of the words within the FQN or path, excluding
            # stop words. These words are not stemmed.
            if action in ('Package', 'Imports', 'Extends', 'Implements',
                          'Method declaration', 'Constructor invocation',
                          'Method invocation', 'Variable declaration',
                          'Variable type'):
                for word in self.getWordNodes_splitNoStem(target, self.stopWords):
                    self.graph.add_edge(target, word)
                    if self.VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]
        
                for word in self.getWordNodes_splitNoStem(referrer, self.stopWords):
                    self.graph.add_edge(referrer, word)
                    if self.VERBOSE_BUILD: print "\tAdding edge from", referrer, "to", word[1]
        
            # Case 2: For new packages, we want to connect the last part of the
            # package's name to the path containing the package (which should have
            # been added by the referrer of 'Package' in the step above).
            elif action in ('New package'):
                for word in self.getWordNodes_splitNoStem(target, self.stopWords):
                    self.graph.add_edge(target, word)
                    if self.VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]
        
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
                for word in self.getWordNodes_splitNoStem(referrer, self.stopWords):
                    self.graph.add_edge(target, word)
                    if self.VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]
        
                for word in self.getWordNodes_splitCamelAndStem(referrer, self.stopWords):
                    self.graph.add_edge(target, word)
                    if self.VERBOSE_BUILD: print "\tAdding edge from", target, "to", word[1]
        c.close()
        conn.close()
        
   # def __loadTopologyNodes(self, conn):
        
   # def __loadAdjacencyNodes(self, conn):
    #==============================================================================#
    # Helper methods for building the graph                                        #
    #==============================================================================#
    
    def getWordNodes_splitNoStem(self, s, stopWords):
        # Returns a list of word nodes from the given string after stripping all
        # non-alphanumeric characters. A word node is a tuple containing 'word' and
        # a String containing the word. Words are always lower case. No stemming is
        # done in this case.
        return [('word', word.lower()) \
                    for word in re.split(r'\W+|\s+', s) \
                    if word != '' and word.lower() not in stopWords]
    
    def getWordNodes_splitCamelAndStem(self, s, stopWords):
        # Returns a list of word nodes from the given string after stripping all
        # non-alphanumeric characters, splitting camel case and stemming each word.
        # A word node is a tuple that contains 'word' and a String containing the
        # word. Words are always lower case.
        return [('word', PorterStemmer().stem(word).lower()) \
                    for word in self.splitCamelWords(s, stopWords) \
                    if word.lower() not in stopWords]
    
    def splitCamelWords(self, s, stopWords):
        # Split camel case words. E.g.,
        # camelSplit("HelloWorld.java {{RSSOwl_AtomFeedLoader}}")
        # --> ['Hello', 'World', 'java', 'RSS', 'Owl', 'Atom', 'Feed', 'Loader']
        result = []
        last = 0
        for match in self.REGEX_SPLIT_CAMEL_CASE.finditer(s):
            if s[last:match.start()] != '':
                result.append(s[last:match.start()])
            last = match.end()
    
        if s[last:] != '':
            result.append(s[last:])
    
        return result
   
class PFIGNode(object):
    
    class NodeType(object):
        PACKAGE = 0
        CLASS = 1
        METHOD = 2
        VARIABLE = 3
        IMPORT = 4
        EXTENDS = 5
        PROJECT = 6
        WORD = 7
        
    def __init__(self, nodeType, value):
        self.nodeType = nodeType
        self.value = value
    
        
    
        