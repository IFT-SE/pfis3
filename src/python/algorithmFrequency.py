from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction
import operator

class Frequency(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, fileName):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName)
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        self.__getOrderedFrequentMethods(navPath, navNumber)
        navToPredict = navPath.navigations[navNumber]
        
        if not navToPredict.isToUnknown():
            # methodToPredict is the method we want to predict
            methodToPredict = navToPredict.toFileNav.methodFqn
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            
            for methodFqn in self.__methodFrequencies:
                if methodFqn == methodToPredict:
                    result = self.__methodFrequencies[methodFqn]
                    
                    sortedRanks = sorted(self.__methodFrequencies, key = lambda freq: self.__methodFrequencies[freq])
                    firstIndex = self.__getFirstIndex(sortedRanks, result)
                    lastIndex = self.__getLastIndex(sortedRanks, result)
                    numTies = lastIndex - firstIndex + 1
                    rankWithTies = self.getRankConsideringTies(firstIndex + 1, numTies)
                
                    return PredictionEntry(navNumber, rankWithTies, len(self.__methodFrequencies), 0,
                                           fromMethodFqn,
                                           methodToPredict,
                                           navToPredict.toFileNav.timestamp)
        
            return PredictionEntry(navNumber, 999999, len(self.__methodFrequencies), 0,
                               str(navToPredict.fromFileNav), 
                               str(navToPredict.toFileNav),
                               navToPredict.toFileNav.timestamp)
        
    
    def __getOrderedFrequentMethods(self, navPath, navNum):
        
        for i in range(navNum + 1):
            nav = navPath.navigations[i]
            if nav.fromFileNav is not None:
                visitedMethod = nav.fromFileNav.methodFqn
                if visitedMethod in self.__methodFrequencies:
                    self.__methodFrequencies[visitedMethod] += 1
                else:
                    self.__methodFrequencies[visitedMethod] = 1

    def __getFirstIndex(self, sortedRankList, value):
        for i in range(0, len(sortedRankList)):
            if self.__methodFrequencies[sortedRankList[i]] == value: return i
        return -1
    
    def __getLastIndex(self, sortedRankList, value):
        for i in range(len(sortedRankList) - 1, -1, -1):
            if self.__methodFrequencies[sortedRankList[i]] == value: return i
        return -1
