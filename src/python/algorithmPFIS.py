from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry
from pfisGraph import NodeType

class PFIS(PredictiveAlgorithm):
    
    # TODO: Initial words should be stemmed before they are activated
        
    def __init__(self, langHelper, name, history=False, goal=[], decayFactor = 0.85, decayHistory = 0.9, numSpread = 20):
        PredictiveAlgorithm.__init__(self, langHelper, name)
        self.history = history
        self.goal = goal
        self.DECAY_FACTOR = decayFactor
        self.DECAY_HISTORY = decayHistory
        self.mapNodesToActivation = None
        self.NUM_SPREAD = numSpread
        
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
            
            # TODO: Discuss how we should go about spreading activation. The two
            # part approach no longer sits well with David
            for _ in range(self.NUM_SPREAD):
                self.__spreadActivation(pfisGraph)
            
            sortedMethods = self.__getMethodNodesFromGraph(pfisGraph, fromMethodFqn)
                
            if methodToPredict in sortedMethods:
                rank = sortedMethods.index(methodToPredict) + 1
                return PredictionEntry(navNumber, rank, len(sortedMethods), 
                       str(navToPredict.fromFileNav), 
                       str(navToPredict.toFileNav),
                       self.langHelper.between_class(fromMethodFqn, methodToPredict),
                       self.langHelper.between_package(fromMethodFqn, methodToPredict),
                       navToPredict.toFileNav.timestamp)
                
        return PredictionEntry(navNumber, 999999, len(sortedMethods), 
                       str(navToPredict.fromFileNav), 
                       str(navToPredict.toFileNav),
                       False, False,
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
                if word in pfisGraph.graph.node:
                    if pfisGraph.graph.node[word]['type'] == NodeType.WORD:
                        self.mapNodesToActivation[word] = 1.0
                    
    def __spreadActivation(self, pfisGraph):
        for node in self.mapNodesToActivation.keys():
            if node not in pfisGraph.graph.node:
                continue
            
            neighbors = pfisGraph.graph.neighbors(node)
            #print '# of neighbors of ' + node + ': ' + str(len(neighbors))
            edgeWeight = 1.0 / len(neighbors)
            for neighbor in neighbors:
                if neighbor not in self.mapNodesToActivation:
                    self.mapNodesToActivation[neighbor] = 0.0
                
                self.mapNodesToActivation[neighbor] = self.mapNodesToActivation[neighbor] + (self.mapNodesToActivation[node] * edgeWeight * self.DECAY_FACTOR)
    
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
                
        