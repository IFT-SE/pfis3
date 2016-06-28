from algorithmPFISBase import PFISBase

class PFIS(PFISBase):

    VERBOSE = 0
    DEBUG_NODE = 'L/hexcom/Current/js_v9/main.js;.init(b)'

    def __init__(self, langHelper, name, fileName, history=False, goal = [], 
                 decayFactor = 0.85, decayHistory = 0.9, numSpread = 2,
                 includeTop = False, numTopPredictions=0):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal, 
                          decayFactor, decayHistory, includeTop, numTopPredictions)
        self.NUM_SPREAD = numSpread

    def spreadActivation(self, pfisGraph):
        #self.printNodes(pfisGraph)
        for _ in range(0, self.NUM_SPREAD):
            for node in self.mapNodesToActivation.keys():
                if not pfisGraph.containsNode(node):
                    continue
                
                neighbors = pfisGraph.getAllNeighbors(node)
                edgeWeight = 1.0 / len(neighbors)
                for neighbor in neighbors:
                    if neighbor not in self.mapNodesToActivation:
                        self.mapNodesToActivation[neighbor] = 0.0


                    if PFIS.VERBOSE and neighbor == PFIS.DEBUG_NODE:
                        print "------------------------------"
                        print "Node:", node, self.mapNodesToActivation[node]
                        print "Neighbor count: ",len(neighbors)
                        print "Standard decay fator:", self.DECAY_FACTOR
                        print "Std spread", self.mapNodesToActivation[node] * self.DECAY_FACTOR
                        print "EdgeWeight due to neighbors decay : 1/ neighbor_count: ", edgeWeight
                        print "Spread incl edge weight: ", (self.mapNodesToActivation[node] * edgeWeight * self.DECAY_FACTOR)
                        print "Neighbor:", neighbor, self.mapNodesToActivation[neighbor]

                    self.mapNodesToActivation[neighbor] = self.mapNodesToActivation[neighbor] + \
                                                          (self.mapNodesToActivation[node] * edgeWeight * self.DECAY_FACTOR)

                    if PFIS.VERBOSE and neighbor == PFIS.DEBUG_NODE:
                        print "Final neighbor weight", self.mapNodesToActivation[neighbor]

                    # Add Verbose flag check
                #if PFIS.VERBOSE:
                    #self.printNodes(pfisGraph)

    def printNodes(self, pfisGraph):
        nodeList = pfisGraph.graph.nodes()
        print "Nodes currently present in the graph along with their weights are:"

        for node in nodeList:
            if  node in  self.mapNodesToActivation:
                print "(",node, " : ", self.mapNodesToActivation[node],")"
            else:
                print "(",node,")"

        print "Total number of nodes currently in the graph are: ", len(nodeList)
