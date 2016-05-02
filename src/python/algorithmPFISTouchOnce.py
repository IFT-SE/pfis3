from algorithmPFISBase import PFISBase
from collections import deque

class PFISTouchOnce(PFISBase):
        
    def __init__(self, langHelper, name, fileName, history=False, goal = [], \
                 decayFactor = 0.85, decayHistory = 0.9, includeTop = False, numTopPredictions=0):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal, 
                          decayFactor, decayHistory, includeTop, numTopPredictions)
        self.history = history
        self.goal = goal
        self.DECAY_FACTOR = decayFactor
        self.DECAY_HISTORY = decayHistory
        self.mapNodesToActivation = None
                     
    def spreadActivation(self, pfisGraph):
        queue = deque()
        
        for node in self.mapNodesToActivation:
            queue.append(node)
        
        while len(queue) > 0:
            currentNode = queue.popleft()
            #TODO: hook up isvariant parameter accordingly
            neighbors = pfisGraph.getAllNeighbors(currentNode)
            edgeWeight = 1.0 / len(neighbors)
            
            for neighbor in neighbors:
                if neighbor not in self.mapNodesToActivation:
                    self.mapNodesToActivation[neighbor] = (self.mapNodesToActivation[node] * edgeWeight * self.DECAY_FACTOR)
                    queue.append(neighbor)

    def computeTargetScores(self, graph, mapNodesToActivation):
        return mapNodesToActivation