from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction
from collections import deque

class CodeStructure(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, fileName, edgeTypes, includeTop = False, numTopPredictions=0):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions)
        self.edgeTypes = edgeTypes
        self.nodeDistances = None
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        navToPredict = navPath.navigations[navNumber]
        fromMethodFqn = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        self.nodeDistances = {}
        sortedRanksMethodsOnly = []
        
        if not navToPredict.isToUnknown() and methodToPredict in pfisGraph.graph.node:
            result = self.__breadthFirstSearch(pfisGraph, fromMethodFqn, methodToPredict) 
            if result > 0:
                sortedRanks = sorted(self.nodeDistances, key = lambda node: self.nodeDistances[node])
                sortedRanksMethodsOnly = self.getRanksForMethodsOnly(sortedRanks, pfisGraph)
                
                firstIndex = self.getFirstIndex(sortedRanksMethodsOnly, self.nodeDistances, result)
                lastIndex = self.getLastIndex(sortedRanksMethodsOnly, self.nodeDistances, result)
                numTies = lastIndex - firstIndex + 1
                rankWithTies = self.getRankConsideringTies(firstIndex + 1, numTies)
                topPredictions = []
                
                if self.includeTop:
                    topPredictions = self.getTopPredictions(sortedRanksMethodsOnly, self.nodeDistances)
                
                return Prediction(navNumber, rankWithTies, len(sortedRanksMethodsOnly), numTies,
                           fromMethodFqn,
                           methodToPredict,
                           navToPredict.toFileNav.timestamp,
                           topPredictions)
        
        return Prediction(navNumber, 999999, len(sortedRanksMethodsOnly), 0,
                           str(navToPredict.fromFileNav),
                           str(navToPredict.toFileNav),
                           navToPredict.toFileNav.timestamp)
    
    def __breadthFirstSearch(self, pfisGraph, fromNode, methodToPredict):
        if fromNode not in pfisGraph.graph.node:
            raise RuntimeError('breadthFirstSearch: Node not found in PFIS Graph: ' + fromNode)
        
        queue = deque()
        self.nodeDistances[fromNode] = 0
        queue.append(fromNode)
        
        while len(queue) > 0:
            
            currentNode = queue.popleft()
            
            for neighbor in self.__getNeighborsOfDesiredEdgeTypes(pfisGraph, currentNode):
                if neighbor not in self.nodeDistances:
                    self.nodeDistances[neighbor] = self.nodeDistances[currentNode] + 1
                    queue.append(neighbor)
                    
        del self.nodeDistances[fromNode]
                    
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
