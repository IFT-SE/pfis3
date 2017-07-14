from algorithmPFISBase import PFISBase
from graphAttributes import NodeType, EdgeType

class PFIS(PFISBase):

    def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal,
                          decayFactor, decaySimilarity, decayVariant, decayHistory, changelogGoalActivation, includeTop, numTopPredictions, verbose)
        self.NUM_SPREAD = numSpread


    def spreadActivation(self, pfisGraph,  fromMethodFqn):
        # This one spreads weights to all neighbors of nodes, but in parallel.
        # This is to prevent double counting the first round spreading during the second spreading round and so on.
        # This is traditional PFIS code, like CHI'10.
        for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)
            accumulator= {}
            for node in self.mapNodesToActivation.keys():
                if i%2 == 0:
                    # Non-words --> word / non-words
                    if pfisGraph.getNode(node)['type'] != NodeType.WORD:
                        allNeighbors = [n for n in pfisGraph.getAllNeighbors(node)]
                        self.spreadTo(pfisGraph, node, allNeighbors, self.mapNodesToActivation, accumulator)
                else:
                    # Word --> non-word types
                    if pfisGraph.getNode(node)['type'] == NodeType.WORD:
                        nonWordNeighbors = [n for n in pfisGraph.getAllNeighbors(node) if pfisGraph.getNode(n)['type'] != NodeType.WORD]
                        self.spreadTo(pfisGraph, node, nonWordNeighbors, self.mapNodesToActivation, accumulator)
            self.mapNodesToActivation.update(accumulator)
        if self.VERBOSE:
            self.printScores(self.mapNodesToActivation, pfisGraph)

    def spreadTo(self, pfisGraph, spreadFrom, neighborsToSpread, priorSpreadResultant, accumulator):
        edgeWeight = 1.0
        decay_factor = 1.0

        # Word --> non-word, do not decay, because non-word to word already does the decay.
        decay = pfisGraph.getNode(spreadFrom)['type'] != NodeType.WORD

        if len(neighborsToSpread) > 0:
            edgeWeight = 1.0 / len(neighborsToSpread)

        for neighbor in neighborsToSpread:
            edge_types = pfisGraph.getEdgeTypesBetween(spreadFrom, neighbor)
            if decay:
                decay_factor = self.getDecayWeight(edge_types)

            if neighbor not in accumulator:
                if neighbor in self.mapNodesToActivation.keys():
                    accumulator[neighbor] = self.mapNodesToActivation[neighbor]
                else:
                    accumulator[neighbor] = 0.0

            neighborWeightBeforeSpread = accumulator[neighbor]
            neighborWeightAfterSpreading = neighborWeightBeforeSpread + (priorSpreadResultant[spreadFrom] * edgeWeight * decay_factor)
            accumulator[neighbor] = neighborWeightAfterSpreading

            if self.VERBOSE:
                print '{} | {} to {}: {} + ({}*{}*{}) = {}'.format(edge_types, spreadFrom, neighbor,
                                                                   neighborWeightBeforeSpread,
                                                                   priorSpreadResultant[spreadFrom], edgeWeight, decay_factor,
                                                                   neighborWeightAfterSpreading)

    def printScores(self, activationMap, graph):
        print "Patch weights for {}".format(self.name)
        for node in activationMap.keys():
            if graph.getNode(node)['type'] in NodeType.predictable():
                print node, " : ", activationMap[node]