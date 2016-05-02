import networkx as nx
import re
import sqlite3

from nltk.stem import PorterStemmer
from knownPatches import KnownPatches
from graphAttributes import NodeType
from graphAttributes import EdgeType

class PfisGraph(object):
    

    SCENT_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN " \
                  "('Package', 'Imports', 'Extends', 'Implements', " \
                  "'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', " \
                  "'Constructor invocation scent', 'Method declaration scent', 'Method invocation scent') " \
                  "AND timestamp >= ? AND timestamp < ?"
    TOPOLOGY_QUERY = "SELECT action, target, referrer FROM logger_log WHERE action IN " \
                     "('Package', 'Imports', 'Extends', 'Implements', " \
                     "'Method declaration', 'Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type') " \
                     "AND timestamp >= ? AND timestamp < ?"
    ADJACENCY_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' " \
                      "AND timestamp >= ? AND timestamp < ? ORDER BY timestamp"
                      
    REGEX_SPLIT_CAMEL_CASE = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')
    

    def __init__(self, dbFilePath, langHelper, projSrc, stopWords=[], verbose=False):
        self.dbFilePath = dbFilePath
        self.langHelper = langHelper
        self.stopWords = stopWords
        self.VERBOSE_BUILD = verbose
        self.graph = nx.Graph()


    def updateGraphByOneNavigation(self, prevEndTimeStamp, newEndTimestamp):
        conn = sqlite3.connect(self.dbFilePath)
        conn.row_factory = sqlite3.Row

        print 'Updating PFIS Graph...'

        self.__addScentNodesUpTo(conn, prevEndTimeStamp, newEndTimestamp)
        self.__addTopologyNodesUpTo(conn, prevEndTimeStamp, newEndTimestamp)
        self.__addAdjacencyNodesUpTo(conn, prevEndTimeStamp, newEndTimestamp)

        print 'Done updating PFIS Graph.'

        conn.close()

    def __addScentNodesUpTo(self, conn, prevEndTimestamp, newEndTimestamp):
        # Inserts nodes into the graph up to a given timestamp in the database
        # provided by the conn.
        print '\tProcessing scent. Adding scent-related nodes...'
        
        c = conn.cursor()
        # if self.VERBOSE_BUILD:
        #     print "\tExecuting scent query from ", self.endTimestamp, "to", newEndTimestamp
        c.execute(self.SCENT_QUERY, [prevEndTimestamp, newEndTimestamp])
        
        for row in c:
            action, target, referrer = \
                row['action'], self.langHelper.fixSlashes(row['target']), \
                self.langHelper.fixSlashes(row['referrer'])
            
            # Note that these can return None if the relation is undefined
            targetNodeType = NodeType.getTargetNodeType(action, target)
            referrerNodeType = NodeType.getReferrerNodeType(action, referrer, self.langHelper)

            # Case 1: target and referrer contain either FQNs or file paths, so
            # create a  node for every target and referrer. Each of these nodes then
            # gets an edge to each of the words within the FQN or path, excluding
            # stop words. These words are not stemmed.
            if action in ('Package', 'Imports', 'Extends', 'Implements',
                          'Method declaration', 'Constructor invocation',
                          'Method invocation', 'Variable declaration',
                          'Variable type'):
                for word in self.__getWordNodes_splitNoStem(target):
                    self._addEdge(target, word, targetNodeType, NodeType.WORD, EdgeType.CONTAINS)
        
                for word in self.__getWordNodes_splitNoStem(referrer):
                    self._addEdge(referrer, word, referrerNodeType, NodeType.WORD, EdgeType.CONTAINS)
        
            # Case 2: These actions have code content within them. In this case we
            # want to add an edge from the FQN node in target to the code content in
            # referrer. The FQNs should already exist because of step 1. Words are
            # added in two ways. In the first pass, the complete word is added,
            # camelCase intact without stemming. In the second pass, the camel case
            # is split, the resulting words are stemmed and those are added to the
            # FQN node.
            elif action in ('Constructor invocation scent',
                            'Method declaration scent',
                            'Method invocation scent'):
                for word in self.__getWordNodes_splitNoStem(referrer):
                    self._addEdge(target, word, targetNodeType, NodeType.WORD, EdgeType.CONTAINS)
                    
                for word in self.getWordNodes_splitCamelAndStem(referrer):
                    self._addEdge(target, word, targetNodeType, NodeType.WORD, EdgeType.CONTAINS)
        c.close()
        
        print '\tDone adding scent-related nodes.'
        self.__printGraphStats()
        
    def __addTopologyNodesUpTo(self, conn, prevEndTimestamp, newEndTimestamp):
        # Build the graph according to the code structure recorded by PFIG. See
        # each section of the build for details.
    
        print "\tProcessing topology. Adding location nodes to the graph..."
    
        c = conn.cursor()
        c.execute(self.TOPOLOGY_QUERY, [prevEndTimestamp, newEndTimestamp])
    
        for row in c:
            action, target, referrer, = \
            row['action'], self.langHelper.fixSlashes(row['target']), \
            self.langHelper.fixSlashes(row['referrer'])
            targetNodeType = NodeType.getTargetNodeType(action, target)
            referrerNodeType = NodeType.getReferrerNodeType(action, referrer, self.langHelper)

            self.updateTopology(action, target, referrer, targetNodeType, referrerNodeType)

        c.close
    
        print "\tDone processing topology."
        self.__printGraphStats()

    def updateTopology(self, action, target, referrer, targetNodeType, referrerNodeType):
        if action == 'Package':
            # target = FILE, referrer = PACKAGE
            # Link the file to the package
            self._addEdge(target, referrer,
                          targetNodeType,
                          referrerNodeType,
                          EdgeType.CONTAINS)
            # Link the package to the root 'Packages' node
            self._addEdge('Packages', referrer,
                          NodeType.SPECIAL,
                          referrerNodeType,
                          EdgeType.CONTAINS)
            # Link the file to its class FQN
            fqn = self.__getClassFQN(target)
            self._addEdge(target, fqn,
                          targetNodeType,
                          NodeType.CLASS,
                          EdgeType.CONTAINS)
        elif action == 'Imports':
            # target = FILE, referrer = CLASS
            # Link the file to its class FQN
            fqn = self.__getClassFQN(target)
            targetPackage = self.langHelper.package(target)
            self._addEdge(target, fqn,
                          targetNodeType,
                          NodeType.CLASS,
                          EdgeType.CONTAINS)
            # Link the class FQN to the imported class
            self._addEdge(fqn, referrer,
                          NodeType.CLASS,
                          referrerNodeType,
                          EdgeType.IMPORTS)
            # Link the file to its package
            self._addEdge(targetPackage, target,
                          NodeType.PACKAGE,
                          targetNodeType,
                          EdgeType.CONTAINS)
            # Link the package to 'Packages'
            self._addEdge('Packages', targetPackage,
                          NodeType.SPECIAL,
                          NodeType.PACKAGE,
                          EdgeType.CONTAINS)
        elif action == 'Extends':
            # target = CLASS, referrer = CLASS
            # Link the class to the class it extends
            self._addEdge(target, referrer,
                          targetNodeType,
                          referrerNodeType,
                          EdgeType.EXTENDS)
        elif action == 'Implements':
            # target = CLASS, referrer = CLASS
            # Link the class to the class it implements
            self._addEdge(target, referrer,
                          targetNodeType,
                          referrerNodeType,
                          EdgeType.IMPLEMENTS)
        elif action == 'Method declaration':
            # target = CLASS, referrer = METHOD
            # Link the class to the method it declares
            self._addEdge(target, referrer,
                          targetNodeType,
                          referrerNodeType,
                          EdgeType.CONTAINS)
        elif action == 'Method invocation':
            # target = METHOD, referrer = METHOD
            # Link the calling method to the called method
            self._addEdge(target, referrer,
                          targetNodeType,
                          referrerNodeType,
                          EdgeType.CALLS)
            # Link the called method to its class
            fqn = self.__getClassFQN(referrer)
            self._addEdge(fqn, referrer,
                          NodeType.CLASS,
                          referrerNodeType,
                          EdgeType.CONTAINS)

        elif action == 'Variable declaration':
            # target = CLASS/METHOD, referrer = VARIABLE
            # Link the variable to the method or class it is defined within
            self._addEdge(target, referrer,
                          targetNodeType,
                          referrerNodeType,
                          EdgeType.CONTAINS)

        elif action == 'Variable type':
            # target = VARIABLE, referrer = CLASS/PRIMITIVE
            # Link the variable to its type
            # TODO: Might have to add variant edges

            self._addEdge(target, referrer,
                          targetNodeType,
                          referrerNodeType,
                          EdgeType.TYPE)

    def __addAdjacencyNodesUpTo(self, conn, prevEndTimestamp, newEndTimestamp):
        knownPatches = KnownPatches(self.langHelper)
    
        print "\tProcessing adjacency. Adding adjacency edges to the graph..."
    
        c = conn.cursor()
        c.execute(self.ADJACENCY_QUERY, [prevEndTimestamp, newEndTimestamp])
        
        for row in c:
            target, referrer = self.langHelper.fixSlashes(row['target']), int(row['referrer'])
            
            knownPatches.addFilePatch(target);
            method = knownPatches.findMethodByFqn(target);
            method.startOffset = referrer
        
        c.close()
        
        adjacentMethodLists = knownPatches.getAdajecentMethods()
        
        for methods in adjacentMethodLists:
            for i in range(1, len(methods)):
                self._addEdge(methods[i].fqn, methods[i - 1].fqn,
                              NodeType.METHOD,
                              NodeType.METHOD,
                              EdgeType.ADJACENT)
#                 print '\t\tAdded edge from '
#                 print '\t\t\t' + methods[i - 1].fqn + ' to '
#                 print '\t\t\t' + methods[i].fqn
        
        print "\tDone processing adjacency."
        self.__printGraphStats()
        
    #==============================================================================#
    # Helper methods for building the graph                                        #
    #==============================================================================#
    
    def _addEdge(self, node1, node2, node1Type, node2Type, edgeType):
        if self.graph.has_edge(node1, node2):
            self.graph.edge[node1][node2]['types'].append(edgeType)
        else:
            self.graph.add_edge(node1, node2, attr_dict={'types': [edgeType]})
            
        self.graph.node[node1]['type'] = node1Type
        self.graph.node[node2]['type'] = node2Type

        if self.VERBOSE_BUILD:
            print "\tAdding edge from", node1, "to", node2, "of type", edgeType

    def __getWordNodes_splitNoStem(self, s):
        # Returns a list of word nodes from the given string after stripping all
        # non-alphanumeric characters. A word node is a tuple containing 'word' and
        # a String containing the word. Words are always lower case. No stemming is
        # done in this case.
        
        return [word.lower() \
                    for word in re.split(r'\W+|\s+', s) \
                    if word != '' and word.lower() not in self.stopWords]
    
    def getWordNodes_splitCamelAndStem(self, s):
        # Returns a list of word nodes from the given string after stripping all
        # non-alphanumeric characters, splitting camel case and stemming each word.
        # A word node is a tuple that contains 'word' and a String containing the
        # word. Words are always lower case.
        
        return [PorterStemmer().stem(word).lower() \
                    for word in self.__splitCamelWords(s) \
                    if word.lower() not in self.stopWords]
    
    def __splitCamelWords(self, s):
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
    
    def __getClassFQN(self, s):
        normalized = self.langHelper.normalize(s)
        
        if normalized != '':
            return 'L' + normalized + ';'
        else:
            raise Exception("convertFilePathToFQN: invalid path: " + s)

    #TODO: move to relevant subclass
    def getVariantNodes(self, node1):
        return self.getNeighborsOfDesiredEdgeTypes(node1, [EdgeType.VARIANT_OF])

    def __printGraphStats(self):
        print "\tGraph contains " + str(len(self.graph.node)) + " nodes."
        print "\tGraph contains " + str(len(self.graph.edge)) + " edges."

    def getNeighborsOfDesiredEdgeTypes(self, node, edgeTypes):
        validNeighbors = []

        for neighbor in self.graph.neighbors(node):
            for edgeType in edgeTypes:
                if edgeType in self.graph[node][neighbor]['types'] and neighbor not in validNeighbors:
                    validNeighbors.append(neighbor)

        return validNeighbors

    #TODO: move to relevant subclass
    def getAllNeighbors(self, node, includeVariantEdges=False):
        edges = EdgeType.getAll()

        if not includeVariantEdges:
            edges.remove(EdgeType.VARIANT_OF)

        return self.getNeighborsOfDesiredEdgeTypes(node, edges)

