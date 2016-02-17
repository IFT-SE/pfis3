from predictiveAlgorithm import PredictiveAlgorithm
from predictions import PredictionEntry
import operator

class Frequency(PredictiveAlgorithm):
        
    def __init__(self, langHelper):
        PredictiveAlgorithm.__init__(self, langHelper)
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        methods = self.__getOrderedFrequentMethods(navPath, navNumber)
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
        
    
    def __getOrderedFrequentMethods(self, navPath, navNum):
        visitedMethods = {}
        
        for i in range(navNum + 1):
            nav = navPath.navigations[i]
            if nav.fromFileNav is not None:
                visitedMethod = nav.fromFileNav.methodFqn
                if visitedMethod in visitedMethods:
                    visitedMethods[visitedMethod] += 1
                else:
                    visitedMethods[visitedMethod] = 1
        
        # Sort methods in visitedMethods (keys) by frequency (values)
       	# sortedMethodsAndFrequencies equals a list of tupes (visitedMethod, frequency) sorted by frequency
        print visitedMethods
        sortedMethodsAndFrequencies = sorted(visitedMethods.items(), key=operator.itemgetter(1))
        print sortedMethodsAndFrequencies
        
        # Get the first element of each tuple (visitedMethod)
        # sortedMethods equals a list of methods sorted by frequency
        sortedMethods = [pair[0] for pair in sortedMethodsAndFrequencies] 
        print sortedMethods
        
        return sortedMethods
