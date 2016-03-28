from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction

class Frequency(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, fileName, includeTop = False, numTopPredictions=0):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions)
        self.__methodFrequencies = {}
     
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
                    firstIndex = self.getFirstIndex(sortedRanks, self.__methodFrequencies, result)
                    lastIndex = self.getLastIndex(sortedRanks, self.__methodFrequencies, result)
                    numTies = lastIndex - firstIndex + 1
                    rankWithTies = self.getRankConsideringTies(firstIndex + 1, numTies)
                    topPredictions = []
                    
                    if self.includeTop:
                        topPredictions = self.getTopPredictions(sortedRanks, self.__methodFrequencies)
                
                    return Prediction(navNumber, rankWithTies, len(self.__methodFrequencies), 0,
                                           fromMethodFqn,
                                           methodToPredict,
                                           navToPredict.toFileNav.timestamp,
                                           topPredictions)
        
        return Prediction(navNumber, 999999, len(self.__methodFrequencies), 0,
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
