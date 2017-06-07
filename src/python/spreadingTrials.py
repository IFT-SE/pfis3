from algorithmPFIS import PFIS
from graphAttributes import NodeType

class PfisSpreadToAllPatches(PFIS):
    def __init__(self, langHelper, name, fileName, history=False, goal=False,
                 decayFactor=0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory=0.9, numSpread=2, changelogGoalActivation=False,
                 includeTop=False, numTopPredictions=0, verbose=False):
        PFIS.__init__(self, langHelper, name, fileName, history, goal,
		              decayFactor, decaySimilarity, decayVariant, decayHistory, numSpread, changelogGoalActivation,
		              includeTop, numTopPredictions, verbose)

    def spreadActivation(self, pfisGraph):
        # Patch is a patch is a patch.
        for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)

            for node in self.mapNodesToActivation.keys():
                if pfisGraph.containsNode(node):
                    if i % 2 == 0:
                        self.spreadToNodesOfType(pfisGraph, node, [NodeType.WORD])
                    else:
                        self.spreadToNodesOfType(pfisGraph, node, NodeType.locationTypes())

            if self.VERBOSE:
                self.printNodes(pfisGraph)

class PfisSpreadWordVariantPatches(PFIS):
    def __init__(self, langHelper, name, fileName, history=False, goal=False,
                 decayFactor=0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory=0.9, numSpread=2, changelogGoalActivation=False,
                 includeTop=False, numTopPredictions=0, verbose=False):
        PFIS.__init__(self, langHelper, name, fileName, history, goal,
                      decayFactor, decaySimilarity, decayVariant, decayHistory, numSpread, changelogGoalActivation,
                      includeTop, numTopPredictions, verbose)

    def spreadActivation(self, pfisGraph):
        # Hierarchy, with spread to variant and back.
        for i in range(0, 3):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)

            for node in self.mapNodesToActivation.keys():
                if pfisGraph.containsNode(node):
                    if i % 3 == 0:
                        self.spreadToNodesOfType(pfisGraph, node, [NodeType.WORD])
                    elif i % 3 == 1:
                        self.spreadToNodesOfType(pfisGraph, node, [NodeType.VARIANT])
                    elif i % 3 == 2:
                        locations = NodeType.locationTypes()
                        locations.remove(NodeType.VARIANT)
                        self.spreadToNodesOfType(pfisGraph, node, locations)

            if self.VERBOSE:
                self.printNodes(pfisGraph)