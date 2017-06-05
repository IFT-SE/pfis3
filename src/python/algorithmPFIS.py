from algorithmPFISBase import PFISBase
from graphAttributes import NodeType, EdgeType

class PFIS(PFISBase):

    DEBUG_NODE = 'L/hexcom/Current/js_v9/main.js;.init(b)'

    def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 includeTop = False, numTopPredictions=0, verbose = False):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal,
                          decayFactor, decaySimilarity, decayVariant, decayHistory, includeTop, numTopPredictions, verbose)
        self.NUM_SPREAD = numSpread

    def spreadActivation0(self, pfisGraph):
        # PFIS3, or CHI'17.
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

        if self.VERBOSE:
            self.printNodes(pfisGraph)

    def spreadActivation1(self, pfisGraph):
        # Patch is a patch is a patch.
        for i in range(0, self.NUM_SPREAD):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)

            for node in self.mapNodesToActivation.keys():
                if pfisGraph.containsNode(node):
                    if i%2 == 0:
                        self.spread(pfisGraph, node, [NodeType.WORD])
                    else:
                        self.spread(pfisGraph, node, NodeType.locationTypes())

            if self.VERBOSE:
                self.printNodes(pfisGraph)

    def spreadActivation(self, pfisGraph):
        # Hierarchy, with spread to variant and back.
        for i in range(0, 3):
            print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)

            for node in self.mapNodesToActivation.keys():
                if pfisGraph.containsNode(node):
                    if i % 3 == 0:
                        self.spread(pfisGraph, node, [NodeType.WORD])
                    elif i%3 == 1:
                        self.spread(pfisGraph, node, [NodeType.VARIANT])
                    elif i%3 == 2:
                        locations = NodeType.locationTypes()
                        locations.remove(NodeType.VARIANT)
                        self.spread(pfisGraph, node, locations)

            if self.VERBOSE:
                self.printNodes(pfisGraph)

    def spread(self, pfisGraph, node, spreadToNodeTypes):
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
