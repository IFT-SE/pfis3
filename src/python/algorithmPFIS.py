from algorithmPFISBase import PFISBase
from graphAttributes import NodeType, EdgeType

class PFIS(PFISBase):

    def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal,
                          decayFactor, decaySimilarity, decayVariant, decayHistory, changelogGoalActivation, includeTop, numTopPredictions, verbose)
        self.NUM_SPREAD = numSpread

    def getSpreadingOrder(self):
        # This method returns what nodes to spread to, for each spreading round.

        wordNodes = [NodeType.WORD]
        patchNodes = NodeType.predictable()
        nonWordOrPatchNodes = set(NodeType.getAll())
        nonWordOrPatchNodes = nonWordOrPatchNodes.difference([NodeType.WORD])
        nonWordOrPatchNodes = nonWordOrPatchNodes.difference(NodeType.predictable())

        return [
            wordNodes,
            nonWordOrPatchNodes,
            patchNodes
            ]
    def spreadActivation(self, pfisGraph, fromMethodFqn=None):

        # This is to spread activation to nodes in parallel, rather than one at a time.
        # The latter has inconsistent order and that affects the spreading of weights.
        # self.mapNodesToActivation keeps the activation to be used for spreading,
        # while accumulator the weights as they get spread.

        accumulator = {}
        accumulator.update(self.mapNodesToActivation)

        for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)

            spreadToNodes = self.getSpreadingOrder()[i % 3]

            for node in self.mapNodesToActivation.keys():
                if pfisGraph.containsNode(node):
                    self.spreadToNodesOfType(pfisGraph, node, spreadToNodes, self.mapNodesToActivation, accumulator)

            self.mapNodesToActivation.update(accumulator)
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
        print "Patch weights: "
        for node in activationMap.keys():
            if graph.getNode(node)['type'] in NodeType.predictable():
                print node, " : ", activationMap[node]