from algorithmPFISBase import PFISBase

class PFIS(PFISBase):
        
    def __init__(self, langHelper, name, fileName, history=False, goal = [], 
                 decayFactor = 0.85, decayHistory = 0.9, numSpread = 2,
                 includeTop = False, numTopPredictions=0):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal, 
                          decayFactor, decayHistory, includeTop, numTopPredictions)
        self.NUM_SPREAD = numSpread

    def computeTargetScores(self, graph, mapNodesToActivation):
        return mapNodesToActivation
                     
    def spreadActivation(self, pfisGraph):
        for _ in range(0, self.NUM_SPREAD):
            for node in self.mapNodesToActivation.keys():
                if node not in pfisGraph.graph.node:
                    continue
                
                neighbors = pfisGraph.getAllNeighbors(node)
                edgeWeight = 1.0 / len(neighbors)
                for neighbor in neighbors:
                    if neighbor not in self.mapNodesToActivation:
                        self.mapNodesToActivation[neighbor] = 0.0
                    # Add Verbose flag check.
                    printNodes(pfisGraph, mapNodesToActivation)
                    self.mapNodesToActivation[neighbor] = self.mapNodesToActivation[neighbor] + (self.mapNodesToActivation[node] * edgeWeight * self.DECAY_FACTOR)

    def printNodes(pfisGraph, mapNodesToActivation):
        nodeList = pfisGraph.nodes()
        print "Nodes currently present in the graph along with their weights are:"

        for node in nodeList:
            if  node in  mapNodesToActivation:
                print "(",node, " : ", mapNodesToActivation[node],")"
            else:
                print "(",node,")"

        print "Total number of nodes currently in the graph are: ", len(nodeList)
