class PredictiveAlgorithm(object):
    
    def __init__(self, langHelper, name):
        self.langHelper = langHelper
        self.name = name
    
    def makePrediction(self, graph, navPath, navNumber):
        raise NotImplementedError('makePrediction: Not Implemented')