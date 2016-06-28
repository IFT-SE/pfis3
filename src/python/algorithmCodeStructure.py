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
        
        if not navToPredict.isToUnknown() and pfisGraph.containsNode(methodToPredict):
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
        if not pfisGraph.containsNode(fromNode):
            raise RuntimeError('breadthFirstSearch: Node not found in PFIS Graph: ' + fromNode)
        
        fromNodeEquivalent = pfisGraph.getFqnOfEquivalentNode(fromNode)
        queue = deque()
        self.nodeDistances[fromNodeEquivalent] = 0
        queue.append(fromNodeEquivalent)
        
        while len(queue) > 0:
            
            currentNode = queue.popleft()
            
            for neighbor in pfisGraph.getNeighborsOfDesiredEdgeTypes(currentNode, self.edgeTypes):
                if neighbor not in self.nodeDistances:
                    self.nodeDistances[neighbor] = self.nodeDistances[currentNode] + 1
                    queue.append(neighbor)
                    
        del self.nodeDistances[fromNodeEquivalent]
                    
        methodToPredictEquivalent = pfisGraph.getFqnOfEquivalentNode(methodToPredict)
        if methodToPredictEquivalent in self.nodeDistances:
            return self.nodeDistances[methodToPredictEquivalent]
        
        return -1