from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry
from pfisGraph import NodeType

class PFIS(PredictiveAlgorithm):
    
    # Todo: Initial words should be stemmed before they are activated
        
    def __init__(self, langHelper, history=False, goal=[], decayFactor = 0.85):
        PredictiveAlgorithm.__init__(self, langHelper)
        self.history = history
        self.goal = goal
        self.DECAY_FACTOR = decayFactor
        self.mapNodesToActivation = None
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')
        
        navToPredict = navPath.navigations[navNumber]
        fromMethodFqn = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        
        print 'Making prediction for navigation: ' + str(navToPredict)
        
        # Reset the graph
        self.mapNodesToActivation = {}
        
        if not self.history:
            # Set the initial node weight
            self.mapNodesToActivation[fromMethodFqn] = 1.0
        else:
            raise NotImplementedError('makePrediction: PFIS with history is not yet available')
        
        self.__initializeGoalWords(pfisGraph)
        
        # Spread activation 20 times
        for _ in range(20):
            self.__spreadActivation(pfisGraph)
        
        sortedMethods = self.__getMethodNodesFromGraph(pfisGraph, fromMethodFqn)
#         print 'Activated method nodes:'
#         for methodFqn in activatedMethodNodes:
#             print '\t' + methodFqn + '\t' + str(self.mapNodesToActivation[methodFqn])
            
        if methodToPredict not in sortedMethods:
            print "No prediction possible. A navigation to unknown location has occurred."
        else:
            rank = sortedMethods.index(methodToPredict) + 1
            print "Prediction possible. Method has rank = " + str(rank)
            print methodToPredict + ' has activation value of ' + str(self.mapNodesToActivation[methodToPredict]) 
        
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
                
    def __initializeGoalWords(self, pfisGraph):
        for word in self.goal:
                if word in pfisGraph.graph.node:
                    if pfisGraph.graph.node[word]['type'] == NodeType.WORD:
                        self.mapNodesToActivation[word] = 1.0
                    
    
    def __getMethodNodesFromGraph(self, pfisGraph, excludeNode):
        activatedMethodNodes = []
        
        for node in self.mapNodesToActivation:
            if node == excludeNode:
                print 'EXCLUDING ' + excludeNode
                continue
            
            if node in pfisGraph.graph.node:
                if pfisGraph.graph.node[node]['type'] == NodeType.METHOD:
                    activatedMethodNodes.append(node)
                    
            sortedNodes = sorted(activatedMethodNodes, key=lambda method: self.mapNodesToActivation[method])
            sortedNodes.reverse()
        return sortedNodes
                
        