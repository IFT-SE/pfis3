from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction
from pfisGraph import NodeType

class PFISBase(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, fileName, history=False, goal = [], \
                 stopWords = [], decayFactor = 0.85, decayHistory = 0.9):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName)
        self.history = history
        self.goal = goal
        self.stopWords = stopWords
        self.DECAY_FACTOR = decayFactor
        self.DECAY_HISTORY = decayHistory
        self.mapNodesToActivation = None
        
    def spreadActivation(self, pfisGraph):
            raise NotImplementedError('spreadActivation is not implemented in PFISBase')
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')
        
        navToPredict = navPath.navigations[navNumber]
        sortedMethods = []
        
        if not navToPredict.isToUnknown():
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            methodToPredict = navToPredict.toFileNav.methodFqn
            
            # Reset the graph
            self.mapNodesToActivation = {}
            
            if not self.history:
                # If there is no history, only activate the fromMethodNode
                self.mapNodesToActivation[fromMethodFqn] = 1.0
            else:
                # If there is history, activate nodes in reverse navigation order
                # using the DECAY_HISTORY property
                self.__initializeHistory(pfisGraph, navPath, navNumber)
            
            self.__initializeGoalWords(pfisGraph)
            
            self.spreadActivation(pfisGraph)
            
            sortedMethods = self.__getMethodNodesFromGraph(pfisGraph, fromMethodFqn)
                
            if methodToPredict in sortedMethods:
                value = self.mapNodesToActivation[methodToPredict]
                firstIndex = self.getFirstIndex(sortedMethods, self.mapNodesToActivation, value)
                lastIndex = self.getLastIndex(sortedMethods, self.mapNodesToActivation, value)
                numTies = lastIndex - firstIndex + 1
                rankWithTies =  self.getRankConsideringTies(firstIndex + 1, numTies)
                
                return Prediction(navNumber, rankWithTies, len(sortedMethods), numTies,
                       str(navToPredict.fromFileNav), 
                       str(navToPredict.toFileNav),
                       navToPredict.toFileNav.timestamp)
                
        return Prediction(navNumber, 999999, len(sortedMethods), 0,
                       str(navToPredict.fromFileNav), 
                       str(navToPredict.toFileNav),
                       navToPredict.toFileNav.timestamp) 

    def __initializeHistory(self, pfisGraph, navPath, navNumber):
        activation = 1.0
        for i in range(navNumber, -1, -1):
            nav = navPath.navigations[i]
            
            if not nav.isToUnknown():
                method = nav.toFileNav.methodFqn
                if method in pfisGraph.graph.node:
                    if pfisGraph.graph.node[method]['type'] == NodeType.METHOD:
                        if method not in self.mapNodesToActivation:
                            # TODO consider making history additive, that is if
                            # a location is visited more than once, sum up its 
                            # weights. This approach keeps the highest 
                            # activation
                            self.mapNodesToActivation[method] = activation
                
            activation *= self.DECAY_HISTORY
            
    def __initializeGoalWords(self, pfisGraph):
        for word in self.goal:
            for stemmedWord in pfisGraph.getWordNodes_splitCamelAndStem(word, self.stopWords):
                if stemmedWord in pfisGraph.graph.node:
                    if pfisGraph.graph.node[stemmedWord]['type'] == NodeType.WORD:
                        self.mapNodesToActivation[stemmedWord] = 1.0
    
    def __getMethodNodesFromGraph(self, pfisGraph, excludeNode):
        activatedMethodNodes = []
        
        for node in self.mapNodesToActivation:
            if node == excludeNode:
                continue
            
            if node in pfisGraph.graph.node:
                if pfisGraph.graph.node[node]['type'] == NodeType.METHOD:
                    activatedMethodNodes.append(node)
                    
            sortedNodes = sorted(activatedMethodNodes, key=lambda method: self.mapNodesToActivation[method])
            sortedNodes.reverse()
        return sortedNodes