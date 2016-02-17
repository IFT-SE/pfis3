from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry
from pfisGraph import EdgeType

class Adjacency(PredictiveAlgorithm):
    
    def __init__(self, langHelper, name):
        PredictiveAlgorithm.__init__(self, langHelper, name)
    
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        navToPredict = navPath.navigations[navNumber]
        fromMethodFqn = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        
        if not navToPredict.isToUnknown() and methodToPredict in pfisGraph.graph.node:
            result = self.__isAdjacent(pfisGraph, fromMethodFqn, methodToPredict) 
            if result > 0:
                return PredictionEntry(navNumber, result, self.__getAdjacentLength(pfisGraph, fromMethodFqn), 
                           fromMethodFqn, 
                           methodToPredict,
                           self.langHelper.between_class(fromMethodFqn, methodToPredict),
                           self.langHelper.between_package(fromMethodFqn, methodToPredict),
                           navToPredict.toFileNav.timestamp)
        
        return PredictionEntry(navNumber, 999999, self.__getAdjacentLength(pfisGraph, fromMethodFqn), 
                           str(navToPredict.fromFileNav), 
                           str(navToPredict.toFileNav),
                           False, False,
                           navToPredict.toFileNav.timestamp)
    
    def __isAdjacent(self, pfisGraph, fromMethod, methodToPredict):
        if fromMethod not in pfisGraph.graph.node:
            raise RuntimeError('isAdjacent: Node not found in PFIS Graph: ' + fromMethod)
        
        adjacentMethods = self.__getNeighborsMarkedAdjacent(pfisGraph, fromMethod)
        
        for method in adjacentMethods:
            result = self.__searchFor(pfisGraph, fromMethod, method, methodToPredict)
            if result > 0:
                return result
                
        return -1
    
    def __searchFor(self, pfisGraph, fromMethod, currentMethod, methodToFind):
        if currentMethod == methodToFind: return 1
        
        adjacentMethods = self.__getNeighborsMarkedAdjacent(pfisGraph, currentMethod)
        
        for method in adjacentMethods:
            if method == fromMethod: continue
            else:
                return 1 + self.__searchFor(pfisGraph, currentMethod, method, methodToFind)
        return -1
    
    def __getAdjacentLength(self, pfisGraph, currentMethod):
        adjacentMethods = self.__getNeighborsMarkedAdjacent(pfisGraph, currentMethod)
        total = 0
        
        for method in adjacentMethods:
            total += self.__getAdjacentLengthHelper(pfisGraph, currentMethod, method)
            
        return total
    
    def __getAdjacentLengthHelper(self, pfisGraph, fromMethod, currentMethod):
        adjacentMethods = self.__getNeighborsMarkedAdjacent(pfisGraph, currentMethod)
        
        if len(adjacentMethods) == 1 and adjacentMethods[0] == fromMethod:
            return 1
        
        for method in adjacentMethods:
            if method == fromMethod: continue
            else:
                return 1 + self.__getAdjacentLengthHelper(pfisGraph, currentMethod, method)
        
        return 0
        
    
    def __getNeighborsMarkedAdjacent(self, pfisGraph, node):
        adjacentNeighbors = []
        
        for neighbor in pfisGraph.graph.neighbors(node):
            if EdgeType.ADJACENT in pfisGraph.graph[node][neighbor]['types']:
                adjacentNeighbors.append(neighbor)
                
        return adjacentNeighbors
            
        