from algorithmPFISBase import PFISBase
from graphAttributes import NodeType, EdgeType

class PFIS(PFISBase):

    def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal,
                          decayFactor, decaySimilarity, decayVariant, decayHistory, changelogGoalActivation, includeTop, numTopPredictions, verbose)
        self.NUM_SPREAD = numSpread

    def spreadActivation(self, pfisGraph):
        spread2Nodes = set(NodeType.getAll())
        spread2Nodes.difference([NodeType.WORD])
        spread2Nodes.difference(NodeType.predictable())

        for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)
            for node in self.mapNodesToActivation.keys():
                if pfisGraph.containsNode(node):
                    if i % 3 == 0:
                        self.spreadToNodesOfType(pfisGraph, node, [NodeType.WORD])
                    elif i % 3 == 1:
                        self.spreadToNodesOfType(pfisGraph, node, spread2Nodes)
                    else:
                        self.spreadToNodesOfType(pfisGraph, node, NodeType.predictable())
        if self.VERBOSE:
            self.printScores()

    def spreadToNodesOfType(self, pfisGraph, node, spreadToNodeTypes):
        edgeWeight = 1.0
        neighborsToSpread = pfisGraph.getNeighborsWithNodeTypes(node, spreadToNodeTypes)

        if len(neighborsToSpread) > 0:
            edgeWeight = 1.0 / len(neighborsToSpread)

        for neighbor in neighborsToSpread:
            edge_types = pfisGraph.getEdgeTypesBetween(node, neighbor)
            decay_factor = self.getDecayWeight(edge_types)

            if neighbor not in self.mapNodesToActivation:
                self.mapNodesToActivation[neighbor] = 0.0

            originalWeight = self.mapNodesToActivation[neighbor]
            updatedWeight = originalWeight + (self.mapNodesToActivation[node] * edgeWeight * decay_factor)
            self.mapNodesToActivation[neighbor] = updatedWeight

            if self.VERBOSE:
                print '{} | {} to {}: {} + ({}*{}*{}) = {}'.format(edge_types, node, neighbor,
                                                                   originalWeight,
                                                                   self.mapNodesToActivation[node],
                                                                   edgeWeight, decay_factor, updatedWeight)
    def printScores(self):
        nodeList = self.mapNodesToActivation.keys()
        for node in nodeList:
                print "(",node, " : ", self.mapNodesToActivation[node],")"