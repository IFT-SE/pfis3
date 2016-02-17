class PredictiveAlgorithm(object):
    
    def __init__(self, langHelper, name):
        self.langHelper = langHelper
        self.name = name
    
    def makePrediction(self, graph, navPath, navNumber):
        raise NotImplementedError('makePrediction: Not Implemented')
    
    def getRankConsideringTies(self, firstPosition, numTies):
        # Note that this is one-based counting
        ranks = range(firstPosition, firstPosition + numTies)
        return float(sum(ranks)) / len(ranks)
        