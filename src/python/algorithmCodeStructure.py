from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry

class CodeStructure(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, edgeTypes):
        PredictiveAlgorithm.__init__(self, langHelper, name)
        self.edgeTypes = edgeTypes
        self.visitedNodes = None
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        navToPredict = navPath.navigations[navNumber]
        fromMethodFqn = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        
        if not navToPredict.isToUnknown() and methodToPredict in pfisGraph.graph.node:
            self.visitedNodes = []
            result = self.__isConnected(pfisGraph, fromMethodFqn, methodToPredict) 
            if result > 0:
                return PredictionEntry(navNumber, result, len(self.visitedNodes),
                           fromMethodFqn,
                           methodToPredict,
                           self.langHelper.between_class(fromMethodFqn, methodToPredict),
                           self.langHelper.between_package(fromMethodFqn, methodToPredict),
                           navToPredict.toFileNav.timestamp)
        
        return PredictionEntry(navNumber, 999999, len(self.visitedNodes),
                           str(navToPredict.fromFileNav),
                           str(navToPredict.toFileNav),
                           False, False,
                           navToPredict.toFileNav.timestamp)
    
    def __isConnected(self, pfisGraph, fromNode, methodToPredict):
        if fromNode not in pfisGraph.graph.node:
            raise RuntimeError('isConnected: Node not found in PFIS Graph: ' + fromNode)
        
        validNeighbors = self.__getNeighborsOfDesiredEdgeTypes(pfisGraph, fromNode)
        
        for neighbor in validNeighbors:
            if neighbor in self.visitedNodes: continue
            result = self.__searchFor(pfisGraph, fromNode, neighbor, methodToPredict)
            if result > 0:
                return result
                
        return -1
    
    def __searchFor(self, pfisGraph, fromNode, currentNode, methodToFind):
        self.visitedNodes.append(currentNode)
        
        if currentNode == methodToFind: return 1
        
        validNeighbors = self.__getNeighborsOfDesiredEdgeTypes(pfisGraph, currentNode)
        
        for neighbor in validNeighbors:
            if neighbor in self.visitedNodes: continue
            else:
                return 1 + self.__searchFor(pfisGraph, currentNode, neighbor, methodToFind)
        return -1
        
    
    def __getNeighborsOfDesiredEdgeTypes(self, pfisGraph, node):
        validNeighbors = []
        
        for neighbor in pfisGraph.graph.neighbors(node):
            for edgeType in self.edgeTypes:
                if edgeType in pfisGraph.graph[node][neighbor]['types'] and neighbor not in validNeighbors:
                    validNeighbors.append(neighbor)
                
        return validNeighbors
