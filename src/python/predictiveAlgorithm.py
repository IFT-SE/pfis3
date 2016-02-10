class PredictiveAlgorithm(object):

    def __init__(self, navPath, graph):
        self.__graph = graph
        self.__navPath = navPath
        
    def getPredictionAt(self, navNum):
        # Should return a PredictionEntry for a specified navigation where navNum > 0
        raise NotImplementedError("getPredictionAt: Not Implemented")
    
    def getAllPredictions(self):
        # Should return a list of PredictionEntries from navigation 1 onwards
        raise NotImplementedError("getAllPredictions: Not Implemented")
        