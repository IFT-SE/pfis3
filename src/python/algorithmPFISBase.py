from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction
from pfisGraph import NodeType

class PFISBase(PredictiveAlgorithm):

    def __init__(self, langHelper, name, fileName, history=False, goal = [], \
                 decayFactor = 0.85, decayHistory = 0.9,
                 includeTop = False, numTopPredictions=0):
        PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions)
        self.history = history
        self.goal = goal
        self.DECAY_FACTOR = decayFactor
        self.DECAY_HISTORY = decayHistory
        self.mapNodesToActivation = None

    def spreadActivation(self, pfisGraph):
        raise NotImplementedError('spreadActivation is not implemented in PFISBase')

    def makePrediction(self, pfisGraph, navPath, navNumber):
        if navNumber < 1 or navNumber >= navPath.getLength():
            raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')

        navToPredict = navPath.navigations[navNumber]
        sortedMethods = []

        if not navToPredict.isToUnknown():
            fromMethodFqn = navToPredict.fromFileNav.methodFqn
            methodToPredict = navToPredict.toFileNav.methodFqn

            self.initialize(fromMethodFqn, navNumber, navPath, pfisGraph)
            self.spreadActivation(pfisGraph)

            if self.mapNodesToActivation == None:
                print "Map was empty!!!!!!!!"
                print self.name

            sortedMethods = self.__getMethodNodesFromGraph(pfisGraph, pfisGraph.getFqnOfEquivalentNode(fromMethodFqn))
            topPredictions = []

            if self.includeTop:
                topPredictions = self.getTopPredictions(sortedMethods, self.mapNodesToActivation)

            equivalentMethod = pfisGraph.getFqnOfEquivalentNode(methodToPredict)
            if equivalentMethod in sortedMethods:
                ranking = self.getRankForMethod(equivalentMethod, sortedMethods, self.mapNodesToActivation)

                return Prediction(navNumber, ranking["rankWithTies"], len(sortedMethods), ranking["numTies"],
                                  str(navToPredict.fromFileNav),
                                  str(navToPredict.toFileNav),
                                  navToPredict.toFileNav.timestamp,
                                  topPredictions)

        return Prediction(navNumber, 999999, len(sortedMethods), 0,
                          str(navToPredict.fromFileNav),
                          str(navToPredict.toFileNav),
                          navToPredict.toFileNav.timestamp)

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
            nav = navPath.navigations[i]

            if not nav.isToUnknown():
                method = nav.fromFileNav.methodFqn
                if pfisGraph.containsNode(method):
                    if pfisGraph.getNode(method)['type'] == NodeType.METHOD:
                        if method not in self.mapNodesToActivation:
                            # TODO consider making history additive, that is if
                            # a location is visited more than once, sum up its 
                            # weights. This approach keeps the highest 
                            # activation
                            self.mapNodesToActivation[method] = activation

            activation *= self.DECAY_HISTORY

    def __initializeGoalWords(self, pfisGraph):
        for word in self.goal:
            for stemmedWord in pfisGraph.getWordNodes_splitCamelAndStem(word):
                if pfisGraph.containsNode(stemmedWord):
                    if pfisGraph.getNode(stemmedWord)['type'] == NodeType.WORD:
                        self.mapNodesToActivation[stemmedWord] = 1.0

    def __getMethodNodesFromGraph(self, pfisGraph, excludeNode):
        activatedMethodNodes = []
        sortedNodes = []

        for node in self.mapNodesToActivation:
            if node == excludeNode:
                continue

            if pfisGraph.containsNode(node):
                #self.langHelper.excludeMethod(node): this can be added as a node attribute itself
                if pfisGraph.getNode(node)['type'] == NodeType.METHOD \
                        and not self.langHelper.excludeMethod(node):
                    activatedMethodNodes.append(node)

            sortedNodes = sorted(activatedMethodNodes, key=lambda method: self.mapNodesToActivation[method], reverse = True)
        return sortedNodes
