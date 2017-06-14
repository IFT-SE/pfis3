from algorithmPFISBase import PFISBase
from collections import deque

class PFISTouchOnce(PFISBase):
        
    def __init__(self, langHelper, name, fileName, history=False, goal = False, \
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, changelogGoalActivation=False, includeTop = False, numTopPredictions=0):
        PFISBase.__init__(self, langHelper, name, fileName, history, goal, 
                          decayFactor, decaySimilarity, decayVariant, decayHistory, changelogGoalActivation, includeTop, numTopPredictions)

    def spreadActivation(self, pfisGraph, fromMethodFqn=None):
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
