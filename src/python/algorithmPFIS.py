from algorithmPFISBase import PFISBase

class PFIS(PFISBase):

    DEBUG_NODE = 'L/hexcom/Current/js_v9/main.js;.init(b)'

    def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 includeTop = False, numTopPredictions=0, verbose = False):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal,
                          decayFactor, decaySimilarity, decayVariant, decayHistory, includeTop, numTopPredictions, verbose)
        self.NUM_SPREAD = numSpread

    def spreadActivation(self, pfisGraph):
        for _ in range(0, self.NUM_SPREAD):
            for node in self.mapNodesToActivation.keys():
                if not pfisGraph.containsNode(node):
                    continue
                neighbors = pfisGraph.getAllNeighbors(node)

                edgeWeight = 1.0 / len(neighbors)
                for neighbor in neighbors:
                    if neighbor not in self.mapNodesToActivation:
                        self.mapNodesToActivation[neighbor] = 0.0

                    edge_types = pfisGraph.getEdgeTypesBetween(node, neighbor)
                    decay_factor = self.getDecayWeight(edge_types)
                    updatedWeight = self.mapNodesToActivation[neighbor] + (self.mapNodesToActivation[node] * edgeWeight * decay_factor)

                    if self.VERBOSE and neighbor == PFIS.DEBUG_NODE:
                        print "------------------------------"
                        print "Node:", node, self.mapNodesToActivation[node]
                        print "Neighbor count: ",len(neighbors)
                        print "Standard decay fator:", decay_factor
                        print "Std spread", self.mapNodesToActivation[node] * decay_factor
                        print "EdgeWeight due to neighbors decay : 1/ neighbor_count: ", edgeWeight
                        print "Spread incl edge weight: ", (self.mapNodesToActivation[node] * edgeWeight * decay_factor)
                        print "Neighbor:", neighbor, self.mapNodesToActivation[neighbor]
                        print "Final neighbor weight", updatedWeight

                    self.mapNodesToActivation[neighbor] = updatedWeight

            if self.VERBOSE:
                self.printNodes(pfisGraph)

    def printNodes(self, pfisGraph):
        nodeList = pfisGraph.graph.nodes()
        print "Nodes currently present in the graph along with their weights are:"

        for node in nodeList:
            if  node in  self.mapNodesToActivation:
                print "(",node, " : ", self.mapNodesToActivation[node],")"
            else:
                print "(",node,")"

        print "Total number of nodes currently in the graph are: ", len(nodeList)
