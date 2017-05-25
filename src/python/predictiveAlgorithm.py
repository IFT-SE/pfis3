from pfisGraph import NodeType
class PredictiveAlgorithm(object):
    def __init__(self, langHelper, name, fileName, includeTop=False, numTopPredictions=0, verbose=False):
        self.langHelper = langHelper
        self.name = name
        self.fileName = fileName
        self.includeTop = includeTop

        self.numTopPredictions= numTopPredictions

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
    
    def getRanksForMethodsOnly(self, sortedRankList, pfisGraph):
        methods = []
        for node in sortedRankList:
            if self.langHelper.isNavigablePatch(node):
                methods.append(node)
        return methods

    def getRankForMethod(self, method, sortedRankList, mapNodeToRank):
        value = mapNodeToRank[method]
        firstIndex = self.getFirstIndex(sortedRankList, mapNodeToRank, value)
        lastIndex = self.getLastIndex(sortedRankList, mapNodeToRank, value)
        numTies = lastIndex - firstIndex + 1
        rankWithTies =  self.getRankConsideringTies(firstIndex + 1, numTies)
        return {"rankWithTies": rankWithTies, "numTies":numTies}

    
    def getTopPredictions(self, sortedRankList, mapNodeToRank):
        numTopPredictions = self.numTopPredictions
        if len(sortedRankList) < numTopPredictions:
            numTopPredictions = len(sortedRankList)

        lastTargetAmongTop = sortedRankList[numTopPredictions - 1]
        leastScoreAmongTop = mapNodeToRank[lastTargetAmongTop]

        topTargets = []

        for i in range(0, numTopPredictions):
            target = sortedRankList[i]
            rank = self.getRankForMethod(target, sortedRankList, mapNodeToRank)["rankWithTies"]
            topTargets.append((target, rank))

        i=numTopPredictions
        while i<len(sortedRankList) and mapNodeToRank[sortedRankList[i]] == leastScoreAmongTop:
            rank = self.getRankForMethod(target, sortedRankList, mapNodeToRank)["rankWithTies"]
            topTargets.append((target, rank))

        return topTargets