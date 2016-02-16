from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry
from pfisGraph import EdgeType

class Adjacency(PredictiveAlgorithm):
    
    def makePrediction(self, pfisGraph, navPath, navNumber):
        navToPredict = navPath.navigations[navNumber]
        if navToPredict.fromFileNav is None:
            raise RuntimeError('makePrediction: Cannot make a prediction for the 1st navigation')
        
        fromMethod = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        print "Predicting:" + str(navToPredict)
        
        if methodToPredict is not None and methodToPredict in pfisGraph.graph.node:
            print "We can make a prediction"
            result = self.__isAdjacent(pfisGraph, fromMethod, methodToPredict) 
            if result > 0:
                print "Methods are adjacent. Length = " + str(result)
        
        else:
            print "We cannot make a prediction"
#             return PredictionEntry(navNumber, 999999, len(methods), 
#                            navToPredict.fromFileNav.toStr(), 
#                            navToPredict.toFileNav.toStr(),
#                            False, False,
#                            navToPredict.toFileNav.timestamp)
    
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
    
    def __getNeighborsMarkedAdjacent(self, pfisGraph, node):
        adjacentNeighbors = []
        
        for neighbor in pfisGraph.graph.neighbors(node):
            if pfisGraph.graph[node][neighbor]['type'] == EdgeType.ADJACENT:
                adjacentNeighbors.append(neighbor)
                
        return adjacentNeighbors
            
        