class PredictiveAlgorithm(object):
    
    def __init__(self, langHelper):
        self.langHelper = langHelper
    
    def makePrediction(self, graph, navPath, navNumber):
        raise NotImplementedError('makePrediction: Not Implemented')
        