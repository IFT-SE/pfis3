from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction

class WorkingSet(PredictiveAlgorithm):
        
    def __init__(self, langHelper, name, fileName, workingSetSize=10, includeTop = False, numTopPredictions=0):
        self.__workingSetSize = workingSetSize
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions)
        
    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath') 
        
        methods = self.__getOrderedRecentMethods(pfisGraph, navPath, navNumber)
        navToPredict = navPath.getNavigation(navNumber)
        
        if not navToPredict.isToUnknown():
            # methodToPredict is the method we want to predict
            methodToPredict = navToPredict.toFileNav.methodFqn
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            
            topPrediction = []
            if self.includeTop:
                topPrediction = [methods[0]]
            
            methodToPredictEquiv = pfisGraph.getFqnOfEquivalentNode(methodToPredict)
            if methodToPredictEquiv in methods:
                rank = methods.index(methodToPredictEquiv)
                return Prediction(navNumber, rank, len(methods), 0,
                                       fromMethodFqn,
                                       methodToPredict,
                                       navToPredict.toFileNav.timestamp,
                                       topPrediction)

        return Prediction(navNumber, 999999, len(methods), 0,
                               str(navToPredict.fromFileNav), 
                               str(navToPredict.toFileNav),
                               navToPredict.toFileNav.timestamp)
        
    def __getOrderedRecentMethods(self, pfisGraph, navPath, navNum):
        visitedMethods = []
        for i in range(0, navNum):
            nav = navPath.getNavigation(i)

            if nav.fromFileNav is not None:
                visitedMethod = nav.fromFileNav.methodFqn
                visitedMethodEquivalent = pfisGraph.getFqnOfEquivalentNode(visitedMethod)
                if visitedMethodEquivalent in visitedMethods:
                    visitedMethods.remove(visitedMethodEquivalent)
                visitedMethods.append(visitedMethodEquivalent)

        visitedMethods.reverse()
        return visitedMethods[0:self.__workingSetSize]


    #TODO: Sruti, Bhargav - remove this is the other one works alright!
    def __getOrderedRecentMethods_obsolete(self, pfisGraph, navPath, navNum):
        visitedMethods = []
        workingSetEndNav = navNum + 1
        workingSetStartNav = 1
        
        if navNum > self.__workingSetSize:
            workingSetStartNav = navNum - self.__workingSetSize + 1

        for i in range(workingSetStartNav, workingSetEndNav):
            nav = navPath.getNavigation(i)
            if nav.fromFileNav is not None:
                visitedMethod = nav.fromFileNav.methodFqn
                visitedMethodEquivalent = pfisGraph.getFqnOfEquivalentNode(visitedMethod)
                if visitedMethodEquivalent in visitedMethods:
                    visitedMethods.remove(visitedMethodEquivalent)
                
                visitedMethods.append(visitedMethodEquivalent)
        visitedMethods.reverse()
        return visitedMethods
