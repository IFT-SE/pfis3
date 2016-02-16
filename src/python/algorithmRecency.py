from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry

class Recency(PredictiveAlgorithm):
        
    def __init__(self, langHelper):
        PredictiveAlgorithm.__init__(self, langHelper)
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        methods = self.__getOrderedRecentMethods(navPath, navNumber)
        navToPredict = navPath.navigations[navNumber]
        
        if not navToPredict.isToUnknown():
            # methodToPredict is the method we want to predict
            methodToPredict = navToPredict.toFileNav.methodFqn
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            
            rank = 0
            for methodFqn in methods:
                if methodFqn == methodToPredict:
                    return PredictionEntry(navNumber, rank, len(methods),
                                           fromMethodFqn,
                                           methodToPredict,
                                           self.langHelper.between_class(fromMethodFqn, methodToPredict),
                                           self.langHelper.between_package(fromMethodFqn, methodToPredict),
                                           navToPredict.toFileNav.timestamp)
                rank += 1
        
        return PredictionEntry(navNumber, 999999, len(methods), 
                               str(navToPredict.fromFileNav), 
                               str(navToPredict.toFileNav),
                               False, False,
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