class PredictiveAlgorithm(object):
    
    def __init__(self, langHelper, name, fileName):
        self.langHelper = langHelper
        self.name = name
        self.fileName = fileName
    
    def makePrediction(self, graph, navPath, navNumber):
        raise NotImplementedError('makePrediction: Not Implemented')
    
    def getRankConsideringTies(self, firstPosition, numTies):
        # Note that this is one-based counting
        ranks = range(firstPosition, firstPosition + numTies)
        return float(sum(ranks)) / len(ranks)
    
    def getFirstIndex(self, sortedRankList, mapNodeToRank, value):
        for i in range(0, len(sortedRankList)):
            if mapNodeToRank[sortedRankList[i]] == value: return i
        return -1
    
    def getLastIndex(self, sortedRankList, mapNodeToRank, value):
        for i in range(len(sortedRankList) - 1, -1, -1):
            if mapNodeToRank[sortedRankList[i]] == value: return i
        return -1