from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry
from collections import deque
from networkx.classes.function import neighbors

class CodeStructure(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, edgeTypes):
        PredictiveAlgorithm.__init__(self, langHelper, name)
        self.edgeTypes = edgeTypes
        self.nodeDistances = None
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        navToPredict = navPath.navigations[navNumber]
        fromMethodFqn = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        
        if not navToPredict.isToUnknown() and methodToPredict in pfisGraph.graph.node:
            self.nodeDistances = {}
            result = self.__breadthFirstSearch(pfisGraph, fromMethodFqn, methodToPredict) 
            if result > 0:
                return PredictionEntry(navNumber, result, len(self.nodeDistances.keys()),
                           fromMethodFqn,
                           methodToPredict,
                           self.langHelper.between_class(fromMethodFqn, methodToPredict),
                           self.langHelper.between_package(fromMethodFqn, methodToPredict),
                           navToPredict.toFileNav.timestamp)
        
        return PredictionEntry(navNumber, 999999, len(self.nodeDistances.keys()),
                           str(navToPredict.fromFileNav),
                           str(navToPredict.toFileNav),
                           False, False,
                           navToPredict.toFileNav.timestamp)
    
    def __breadthFirstSearch(self, pfisGraph, fromNode, methodToPredict):
        if fromNode not in pfisGraph.graph.node:
            raise RuntimeError('isConnected: Node not found in PFIS Graph: ' + fromNode)
        
        queue = deque()
        self.nodeDistances[fromNode] = 0
        queue.append(fromNode)
        
        while len(queue) > 0:
            
            currentNode = queue.popleft()
            
            for neighbor in self.__getNeighborsOfDesiredEdgeTypes(pfisGraph, currentNode):
                if neighbor not in self.nodeDistances:
                    self.nodeDistances[neighbor] = self.nodeDistances[currentNode] + 1
                    queue.append(neighbor)
                    
        if methodToPredict in self.nodeDistances:
            return self.nodeDistances[methodToPredict] 
        
        return -1
    
    def __getNeighborsOfDesiredEdgeTypes(self, pfisGraph, node):
        validNeighbors = []
        
        for neighbor in pfisGraph.graph.neighbors(node):
            for edgeType in self.edgeTypes:
                if edgeType in pfisGraph.graph[node][neighbor]['types'] and neighbor not in validNeighbors:
                    validNeighbors.append(neighbor)
                
        return validNeighbors
