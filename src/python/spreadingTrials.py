from algorithmPFIS import PFIS
from graphAttributes import NodeType

class PFISStartFromCurrentNode(PFIS):
    def __init__(self, langHelper, name, fileName, history=False, goal=False,
                 decayFactor=0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory=0.9, numSpread=2, changelogGoalActivation=False,
                 includeTop=False, numTopPredictions=0, verbose=False):
        PFIS.__init__(self, langHelper, name, fileName, history, goal,
		              decayFactor, decaySimilarity, decayVariant, decayHistory, numSpread, changelogGoalActivation,
		              includeTop, numTopPredictions, verbose)


    def spreadActivation(self, pfisGraph,  fromMethodFqn=None):
        # This is to spread activation to nodes in parallel, rather than one at a time.
        # The latter has inconsistent order and that affects the spreading of weights.
        # self.mapNodesToActivation keeps the activation to be used for spreading,
        # while accumulator the weights as they get spread.

        accumulator = {}
        accumulator.update(self.mapNodesToActivation)

        activationList = [fromMethodFqn]

        for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)
            spreadToTypes = self.getSpreadingOrder()[i % 3]

            for node in activationList:
                if pfisGraph.containsNode(node):
                    self.spreadToNodesOfType(pfisGraph, node, spreadToTypes, self.mapNodesToActivation, accumulator)

            self.mapNodesToActivation.update(accumulator)
            activationList = accumulator.keys()

        if self.VERBOSE:
            self.printScores(self.mapNodesToActivation, pfisGraph)