from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry
class Recency(PredictiveAlgorithm):
    
    def __init__(self, navPath, langHelper):
        self.navPath = navPath
        self.langHelper = langHelper
        
    def getPredictionAt(self, navNum):
        methods = self.__getOrderedRecentMethods(navNum)
        navToPredict = self.navPath.navigations[navNum]
        

        if not navToPredict.isToUnknown():
            # This is the method we want to predict
            toMethodFqn = navToPredict.toFileNav.methodFqn
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            
            rank = 0
            for methodFqn in methods:
                if methodFqn == toMethodFqn:
                    return PredictionEntry(navNum, rank, len(methods),
                                           fromMethodFqn,
                                           toMethodFqn,
                                           self.langHelper.between_class(fromMethodFqn, toMethodFqn),
                                           self.langHelper.between_package(fromMethodFqn, toMethodFqn),
                                           navToPredict.toFileNav.timestamp)
                rank += 1
        
        return PredictionEntry(navNum, 999999, len(methods), 
                               navToPredict.fromFileNav.toStr(), 
                               navToPredict.toFileNav.toStr(),
                               False, False,
                               navToPredict.toFileNav.timestamp)
    
    def getAllPredictions(self):
        raise NotImplementedError("getAllPredictions: Not Implmented")
    
    def __getOrderedRecentMethods(self, navNum):
        visitedMethods = []
        
        for i in range(navNum + 1):
            nav = self.navPath.navigations[i]
            if nav.fromFileNav is not None:
                visitedMethod = nav.fromFileNav.methodFqn
                if visitedMethod in visitedMethods:
                    visitedMethods.remove(visitedMethod)
                
                visitedMethods.append(visitedMethod)
        
        visitedMethods.reverse()
        return visitedMethods