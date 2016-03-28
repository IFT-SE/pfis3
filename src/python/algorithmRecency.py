from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction

class Recency(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, fileName, includeTop = False, numTopPredictions=0):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions)
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        methods = self.__getOrderedRecentMethods(navPath, navNumber)
        navToPredict = navPath.navigations[navNumber]
        
        if not navToPredict.isToUnknown():
            # methodToPredict is the method we want to predict
            methodToPredict = navToPredict.toFileNav.methodFqn
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            
            topPrediction = []
            if self.includeTop:
                topPrediction = [methods[0]]
            
            rank = 1
            for methodFqn in methods:
                if methodFqn == methodToPredict:
                    return Prediction(navNumber, rank, len(methods), 0,
                                           fromMethodFqn,
                                           methodToPredict,
                                           navToPredict.toFileNav.timestamp,
                                           topPrediction)
                rank += 1
        
        return Prediction(navNumber, 999999, len(methods), 0,
                               str(navToPredict.fromFileNav), 
                               str(navToPredict.toFileNav),
                               navToPredict.toFileNav.timestamp)
        
    
    def __getOrderedRecentMethods(self, navPath, navNum):
        visitedMethods = []
        
        for i in range(navNum + 1):
            nav = navPath.navigations[i]
            if nav.fromFileNav is not None:
                visitedMethod = nav.fromFileNav.methodFqn
                if visitedMethod in visitedMethods:
                    visitedMethods.remove(visitedMethod)
                
                visitedMethods.append(visitedMethod)
        
        visitedMethods.reverse()
        return visitedMethods
