from algorithmPFISBase import PFISBase

class PFISTouchOnce(PFISBase):
        
    def __init__(self, langHelper, name, fileName, history=False, goal = [], \
                 stopWords = [], decayFactor = 0.85, decayHistory = 0.9, \
                 numSpread = 20):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal, 
                          stopWords, decayFactor, decayHistory)
        self.history = history
        self.goal = goal
        self.stopWords = stopWords
        self.DECAY_FACTOR = decayFactor
        self.DECAY_HISTORY = decayHistory
        self.NUM_SPREAD = numSpread
        self.mapNodesToActivation = None
        self.NUM_SPREAD = numSpread
                     
    def spreadActivation(self, pfisGraph):
        for _ in range(0, self.NUM_SPREAD):
            for node in self.mapNodesToActivation.keys():
                if node not in pfisGraph.graph.node:
                    continue
                
                neighbors = pfisGraph.graph.neighbors(node)
                edgeWeight = 1.0 / len(neighbors)
                for neighbor in neighbors:
                    if neighbor not in self.mapNodesToActivation:
                        self.mapNodesToActivation[neighbor] = (self.mapNodesToActivation[node] * edgeWeight * self.DECAY_FACTOR)
