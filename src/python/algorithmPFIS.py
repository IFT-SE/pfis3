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
        spread2Nodes = spread2Nodes.difference([NodeType.WORD])
        spread2Nodes = spread2Nodes.difference(NodeType.predictable())

        # This is to spread activation to nodes in parallel, rather than one at a time.
        # The latter has inconsistent order and that affects the spreading of weights.
        accumulator = {}
        accumulator.update(self.mapNodesToActivation)

        for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)

            for node in self.mapNodesToActivation.keys():

                if pfisGraph.containsNode(node):
                    currentNodeWeight = self.mapNodesToActivation[node]
                    if i % 3 == 0:
                        self.spreadToNodesOfType(pfisGraph, node, currentNodeWeight, [NodeType.WORD], accumulator)
                    elif i % 3 == 1:
                        self.spreadToNodesOfType(pfisGraph, node, currentNodeWeight, spread2Nodes, accumulator)
                    else:
                        self.spreadToNodesOfType(pfisGraph, node, currentNodeWeight, NodeType.predictable(), accumulator)
            self.mapNodesToActivation.update(accumulator)

        if self.VERBOSE:
            self.printScores(self.mapNodesToActivation, pfisGraph)

    def spreadToNodesOfType(self, pfisGraph, node, initialNodeWeight, spreadToNodeTypes, accumulator):
        edgeWeight = 1.0
        neighborsToSpread = pfisGraph.getNeighborsWithNodeTypes(node, spreadToNodeTypes)

        if len(neighborsToSpread) > 0:
            edgeWeight = 1.0 / len(neighborsToSpread)

        for neighbor in neighborsToSpread:
            edge_types = pfisGraph.getEdgeTypesBetween(node, neighbor)
            decay_factor = self.getDecayWeight(edge_types)

            if neighbor not in self.mapNodesToActivation:
                accumulator[neighbor] = 0.0

            neighborWeightBeforeSpread = accumulator[neighbor]
            neighborWeightAfterSpreading = neighborWeightBeforeSpread + (initialNodeWeight * edgeWeight * decay_factor)
            accumulator[neighbor] = neighborWeightAfterSpreading

            if self.VERBOSE:
                print '{} | {} to {}: {} + ({}*{}*{}) = {}'.format(edge_types, node, neighbor,
                                                                   neighborWeightBeforeSpread,
                                                                   initialNodeWeight, edgeWeight, decay_factor,
                                                                   neighborWeightAfterSpreading)
    def printScores(self, activationMap, graph):
        print "Patch weights: "
        for node in activationMap.keys():
            if graph.getNode(node)['type'] in NodeType.predictable():
                print node, " : ", activationMap[node]