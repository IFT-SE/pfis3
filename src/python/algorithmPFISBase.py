from graphAttributes import EdgeType
from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction
from pfisGraph import NodeType

class PFISBase(PredictiveAlgorithm):

    def __init__(self, langHelper, name, fileName, history=False, goal=False, \
                 decayFactor = 0.85, decayVariants=0.85, decayHistory = 0.9,
                 includeTop = False, numTopPredictions=0, verbose=False):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions, verbose)
        self.history = history
        self.goal = goal
        self.DECAY_FACTOR = decayFactor
        self.DECAY_HISTORY = decayHistory
        self.DECAY_BETWEEN_VARIANTS = decayVariants
        self.mapNodesToActivation = None
        self.VERBOSE = False

    def spreadActivation(self, pfisGraph):
        raise NotImplementedError('spreadActivation is not implemented in PFISBase')

    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')

        navToPredict = navPath.getNavigation(navNumber)
        if navToPredict.isToUnknown():
            return Prediction(navNumber, 999999, 0, 0,
                              str(navToPredict.fromFileNav),
                              str(navToPredict.toFileNav),
                              navToPredict.toFileNav.timestamp)

        fromMethodFqn = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        self.initialize(fromMethodFqn, navNumber, navPath, pfisGraph)

        self.spreadActivation(pfisGraph)

        if self.mapNodesToActivation == None:
            print "Map was empty!!!!!!!!"
            print self.name


        fromMethodEquivalentFqn = pfisGraph.getFqnOfEquivalentNode(fromMethodFqn)
        toMethodEquivalent = pfisGraph.getFqnOfEquivalentNode(methodToPredict)

        if fromMethodEquivalentFqn == toMethodEquivalent and navPath.ifNavToUnseenPatch(navNumber):
            excludeMethod = None
        else:
            excludeMethod = fromMethodEquivalentFqn

        sortedMethods = self.__getMethodNodesFromGraph(pfisGraph, excludeMethod)
        if toMethodEquivalent in sortedMethods:
            ranking = self.getRankForMethod(toMethodEquivalent, sortedMethods, self.mapNodesToActivation)
            topPredictions = []
            if self.includeTop:
                topPredictions = self.getTopPredictions(sortedMethods, self.mapNodesToActivation)

            return Prediction(navNumber, ranking["rankWithTies"], len(sortedMethods), ranking["numTies"],
                              str(navToPredict.fromFileNav),
                              str(navToPredict.toFileNav),
                              navToPredict.toFileNav.timestamp,
                              topPredictions)
        else:
            raise Exception("Node not in activation list: ", toMethodEquivalent)


    def initialize(self, fromMethodFqn, navNumber, navPath, pfisGraph):
        # Reset the graph
        self.mapNodesToActivation = {}

        if not self.history:
            # If there is no history, only activate the fromMethodNode
            fromPatchEquivalent = pfisGraph.getFqnOfEquivalentNode(fromMethodFqn)
            self.mapNodesToActivation[fromPatchEquivalent] = 1.0
        else:
            # If there is history, activate nodes in reverse navigation order
            # using the DECAY_HISTORY property
            self.__initializeHistory(pfisGraph, navPath, navNumber)

        self.__initializeGoalWords(pfisGraph)


    def __initializeHistory(self, pfisGraph, navPath, navNumber):
        activation = 1.0
        # Stop before the first navigation
        for i in range(navNumber, 0, -1):
            nav = navPath.getNavigation(i)

            method = nav.fromFileNav.methodFqn
            if pfisGraph.containsNode(method):
                if self.langHelper.isNavigablePatch(method):
                    if method not in self.mapNodesToActivation:
                        # TODO consider making history additive, that is if
                        # a location is visited more than once, sum up its
                        # weights. This approach keeps the highest
                        # activation
                        self.mapNodesToActivation[method] = activation
                        if self.VERBOSE:
                            print "History: ", method, " ", activation

            activation *= self.DECAY_HISTORY

    def __initializeGoalWords(self, pfisGraph):
        if self.goal:
            for stemmedWord in pfisGraph.getGoalWords():
                if pfisGraph.containsNode(stemmedWord):
                    if pfisGraph.getNode(stemmedWord)['type'] == NodeType.WORD:
                        self.mapNodesToActivation[stemmedWord] = 1.0


    def __getMethodNodesFromGraph(self, pfisGraph, excludeNode=None):
        activatedMethodNodes = []
        sortedNodes = []

        for node in self.mapNodesToActivation:
            if node == excludeNode:
                continue

            if pfisGraph.containsNode(node):
                if self.langHelper.isNavigablePatch(node):
                    activatedMethodNodes.append(node)

            sortedNodes = sorted(activatedMethodNodes, key=lambda method: self.mapNodesToActivation[method], reverse = True)
        return sortedNodes

    def getDecayWeight(self, edgeTypes):
        def getEdgeWeightForType(edgeType):
            if edgeType == EdgeType.VARIANT_OF:
                return self.DECAY_BETWEEN_VARIANTS
            elif edgeType in [EdgeType.ADJACENT, EdgeType.CALLS, EdgeType.CONTAINS]:
                return  self.DECAY_FACTOR
            raise Exception("Invalid Edge Type: ", edgeType)
        return max([getEdgeWeightForType(edgeType) for edgeType in edgeTypes])

