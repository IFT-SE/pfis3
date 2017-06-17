from algorithmPFISBase import PFISBase
from graphAttributes import NodeType, EdgeType

class PFIS(PFISBase):

    def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal,
                          decayFactor, decaySimilarity, decayVariant, decayHistory, changelogGoalActivation, includeTop, numTopPredictions, verbose)
        self.NUM_SPREAD = numSpread


    def spreadActivation(self, pfisGraph,  fromMethodFqn=None):
        # This one spreads weights to all neighbors of nodes, but in parallel.
        # This is to prevent double counting the first round spreading during the second spreading round and so on.
        # This is traditional PFIS code, like CHI'10.

        toSpreadList = self.mapNodesToActivation.keys()
        for i in range(0, self.NUM_SPREAD):
            accumulator = {}
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)
            for node in toSpreadList:
                if pfisGraph.containsNode(node):
                    self.spreadToNodesOfType(pfisGraph, node, NodeType.getAll(), self.mapNodesToActivation, accumulator)

            self.mapNodesToActivation.update(accumulator)
            toSpreadList = accumulator.keys()

        if self.VERBOSE:
            self.printScores(self.mapNodesToActivation, pfisGraph)

    def spreadToNodesOfType(self, pfisGraph, node, spreadToNodeTypes, mapNodesToActivation, accumulator):
        edgeWeight = 1.0
        neighborsToSpread = pfisGraph.getNeighborsWithNodeTypes(node, spreadToNodeTypes)

        if len(neighborsToSpread) > 0:
            edgeWeight = 1.0 / len(neighborsToSpread)

        for neighbor in neighborsToSpread:
            edge_types = pfisGraph.getEdgeTypesBetween(node, neighbor)
            decay_factor = self.getDecayWeight(edge_types)

            if neighbor not in accumulator:
                if neighbor in self.mapNodesToActivation.keys():
                    accumulator[neighbor] = self.mapNodesToActivation[neighbor]
                else:
                    accumulator[neighbor] = 0.0

            neighborWeightBeforeSpread = accumulator[neighbor]
            neighborWeightAfterSpreading = neighborWeightBeforeSpread + (mapNodesToActivation[node] * edgeWeight * decay_factor)
            accumulator[neighbor] = neighborWeightAfterSpreading

            if self.VERBOSE:
                print '{} | {} to {}: {} + ({}*{}*{}) = {}'.format(edge_types, node, neighbor,
                                                                   neighborWeightBeforeSpread,
                                                                   mapNodesToActivation[node], edgeWeight, decay_factor,
                                                                   neighborWeightAfterSpreading)
    def printScores(self, activationMap, graph):
        print "Patch weights for {}: ", self.name
        for node in activationMap.keys():
            if graph.getNode(node)['type'] in NodeType.predictable():
                print node, " : ", activationMap[node]