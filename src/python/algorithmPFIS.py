from algorithmPFISBase import PFISBase
from graphAttributes import NodeType, EdgeType

class PFIS(PFISBase):

    DEBUG_NODE = 'L/hexcom/Current/js_v9/main.js;.init(b)'

    def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal,
                          decayFactor, decaySimilarity, decayVariant, decayHistory, changelogGoalActivation, includeTop, numTopPredictions, verbose)
        self.NUM_SPREAD = numSpread

    def spreadActivation(self, pfisGraph):
        for i  in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i+1, self.NUM_SPREAD)
            for node in self.mapNodesToActivation.keys():
                if not pfisGraph.containsNode(node):
                    continue

                neighbors = pfisGraph.getAllNeighbors(node)
                edgeWeight = 1.0/len(neighbors)

                for neighbor in neighbors:
                    if neighbor not in self.mapNodesToActivation:
                        self.mapNodesToActivation[neighbor] = 0.0

                    originalWeight = self.mapNodesToActivation[neighbor]
                    edge_types = pfisGraph.getEdgeTypesBetween(node, neighbor)
                    decay_factor = self.getDecayWeight(edge_types)
                    updatedWeight = originalWeight + (self.mapNodesToActivation[node] * edgeWeight * decay_factor)
                    self.mapNodesToActivation[neighbor] = updatedWeight

                    if self.VERBOSE:
                        print '{} | {} to {}: {} + ({}*{}*{}) = {}'.format(edge_types, node, neighbor, originalWeight, self.mapNodesToActivation[node], edgeWeight, decay_factor, updatedWeight)

        # if self.VERBOSE:
        #     self.printNodes(pfisGraph)


    def spreadToNodesOfType(self, pfisGraph, node, spreadToNodeTypes):
        edgeWeight = 1.0

        neighbors = pfisGraph.getAllNeighbors(node)
        neighborsToSpread = [n for n in neighbors if pfisGraph.getNode(n)['type'] in spreadToNodeTypes]
        if len(neighborsToSpread) > 0:
            edgeWeight = 1.0 / len(neighbors)

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
                                                                   edgeWeight,
                                                                   decay_factor, updatedWeight)
    def printNodes(self, pfisGraph):
        nodeList = pfisGraph.graph.nodes()
        print "Nodes currently present in the graph along with their weights are:"

        for node in nodeList:
            if  node in  self.mapNodesToActivation:
                print "(",node, " : ", self.mapNodesToActivation[node],")"
            else:
                print "(",node,")"

        print "Total number of nodes currently in the graph are: ", len(nodeList)
