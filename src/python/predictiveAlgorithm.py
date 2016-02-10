class PredictiveAlgorithm(object):

    def __init__(self, navPath, graph):
        self.__graph = graph
        self.__navPath = navPath
        
    def getPredictionAt(self, navNum):
        raise NotImplemented()
    
    def getAllPredictions(self):
        raise NotImplemented()
        