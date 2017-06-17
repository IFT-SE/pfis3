from algorithmPFIS import PFIS
from graphAttributes import NodeType

class PFIS3(PFIS):
     def spreadActivation(self, pfisGraph,  fromMethodFqn=None):
        # PFIS3 and CHI'17 PFIS-V do not spread in parallel.
        # Instead the order in which they spread are decide by order yielded by dictionary.keys()
         for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)
            for node in self.mapNodesToActivation.keys():
                if pfisGraph.containsNode(node):
                    neighbors = pfisGraph.getAllNeighbors(node)

                    edgeWeight = 1.0
                    if len(neighbors) > 0:
                        edgeWeight = 1/len(neighbors)

                    for neighbor in neighbors:
                        edge_types = pfisGraph.getEdgeTypesBetween(node, neighbor)
                        decay_factor = self.getDecayWeight(edge_types)

                        if neighbor not in self.mapNodesToActivation.keys():
                            self.mapNodesToActivation[neighbor] = 0.0

                        self.mapNodesToActivation[neighbor] = self.mapNodesToActivation[neighbor] + \
                                                              (self.mapNodesToActivation[node] * edgeWeight * decay_factor)
            if self.VERBOSE:
                self.printScores(self.mapNodesToActivation, pfisGraph)

class PFISSpreadWordOthersPatches(PFIS):
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