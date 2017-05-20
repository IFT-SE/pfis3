from graphAttributes import EdgeType
from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction
from pfisGraph import NodeType
from patches import ChangelogPatch

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


        elif self._isBetweenVariantNavigation(navPath, navNumber):
            prediction = self._predictBetweenVariantNavigation(pfisGraph, navPath, navNumber)
            if prediction is None:
                raise Exception("SS, BP: Investigate why, else this might be another case of unknown")
            return prediction

        else:
            prediction = self._predictWithinVariantNavigation(pfisGraph, navPath, navNumber)
            if prediction is None:
                raise Exception("SS, BP: Investigate why, else this might be another case of unknown")
            return prediction

    def _isBetweenVariantNavigation(self, navPath, navNumber):
        return False
        navToPredict = navPath.getNavigation(navNumber)

        seenPatches = navPath.getPatchesUpto(navNumber)
        alreadySeenVariants = set([self.langHelper.getVariantName(patch) for patch in seenPatches])

        fromVariant = self.langHelper.getVariantName(navToPredict.fromFileNav.methodFqn)
        toVariant = self.langHelper.getVariantName(navToPredict.toFileNav.methodFqn)

        if fromVariant is None or toVariant is None: #Non-variant topology
            return False
        if fromVariant != toVariant and toVariant not in alreadySeenVariants:
            return True
        return False

    def _predictBetweenVariantNavigation(self, pfisGraph, navPath, navNumber):
        navToPredict = navPath.getNavigation(navNumber)
        fromPatchFqn = navToPredict.fromFileNav.methodFqn
        toPatchFqn = navToPredict.toFileNav.methodFqn

        fromVariant = self.langHelper.getVariantName(fromPatchFqn)
        toVariant = self.langHelper.getVariantName(toPatchFqn)

        fromPatchType = pfisGraph.getNode(fromPatchFqn)['type']

        if fromPatchType == NodeType.METHOD:
            return self._predictWithinVariantNavigation(pfisGraph, navPath, navNumber)

        elif fromPatchType == NodeType.CHANGELOG:
            variantPrediction = self.predictVariant(pfisGraph, fromPatchFqn)

            if variantPrediction is None: #CHangelog said "Not this variant, but something else!"
                if toVariant == fromVariant:
                    # Person went into that variant -- Between-variant MISS
                    return Prediction(navNumber, 888888, 0, 0,
                                  str(navToPredict.fromFileNav),
                                  str(navToPredict.toFileNav),
                                  navToPredict.toFileNav.timestamp)

                else: #Person went into other variant -- Between-variant HIT
                    #Went into similar patch as last seen patch -- within-variant is also a HIT.
                    if self.langHelper.isVariantOf(fromPatchFqn, toPatchFqn):
                        return Prediction(navNumber, 1, 0, 0,
                                  str(navToPredict.fromFileNav),
                                  str(navToPredict.toFileNav),
                                  navToPredict.toFileNav.timestamp)

                    else:
                        # Variant_of did not predict the patch in the new variant -- MISS.
                        return Prediction(navNumber, 888888, 0, 0,
                                  str(navToPredict.fromFileNav),
                                  str(navToPredict.toFileNav),
                                  navToPredict.toFileNav.timestamp)
            else:
                # Forage within the variant, so use normal scent following as in CHI'17 paper.
                return self._predictWithinVariantNavigation(pfisGraph, navPath, navNumber, initializeVariants=False)

    def _predictWithinVariantNavigation(self, pfisGraph, navPath, navNumber, initializeVariants=False):
        navToPredict = navPath.getNavigation(navNumber)
        fromMethodFqn = navToPredict.fromFileNav.methodFqn
        methodToPredict = navToPredict.toFileNav.methodFqn
        self.initialize(fromMethodFqn, navNumber, navPath, pfisGraph, initializeVariants)

        self.spreadActivation(pfisGraph)

        if self.mapNodesToActivation == None:
            print "Map was empty!!!!!!!!"
            print self.name

        fromFQN = pfisGraph.getFqnOfEquivalentNode(fromMethodFqn)
        sortedMethods = self.__getMethodNodesFromGraph(pfisGraph, fromFQN)

        equivalentMethod = pfisGraph.getFqnOfEquivalentNode(methodToPredict)
        if equivalentMethod in sortedMethods:
            ranking = self.getRankForMethod(equivalentMethod, sortedMethods, self.mapNodesToActivation)

            topPredictions = []
            if self.includeTop:
                topPredictions = self.getTopPredictions(sortedMethods, self.mapNodesToActivation)

            return Prediction(navNumber, ranking["rankWithTies"], len(sortedMethods), ranking["numTies"],
                              str(navToPredict.fromFileNav),
                              str(navToPredict.toFileNav),
                              navToPredict.toFileNav.timestamp,
                              topPredictions)


    def initialize(self, fromMethodFqn, navNumber, navPath, pfisGraph, initializeVariants):
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

        if initializeVariants:
            self.__initializeVariants(pfisGraph, fromMethodFqn)

        # self.__removeWordsFromAbandonedChangelogs(pfisGraph, navPath, navNumber)

    def __initializeVariants(self, pfisGraph, fromMethodFqn):
        similarPatches = pfisGraph.getNeighborsOfDesiredEdgeTypes(fromMethodFqn, [EdgeType.VARIANT_OF])
        for node in similarPatches:
            if node not in self.mapNodesToActivation.keys():
                self.mapNodesToActivation[node] = 0.0
            else:
                self.mapNodesToActivation[node] = self.mapNodesToActivation[node] + 10.0

    def __initializeHistory(self, pfisGraph, navPath, navNumber):
        activation = 1.0
        # Stop before the first navigation
        for i in range(navNumber, 0, -1):
            nav = navPath.getNavigation(i)

            method = nav.fromFileNav.methodFqn
            if pfisGraph.containsNode(method):
                if pfisGraph.getNode(method)['type'] in [NodeType.METHOD, NodeType.CHANGELOG]:
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


    def __removeWordsFromAbandonedChangelogs(self, pfisGraph, navPath, navNumber):
        fromPatchFqn = navPath.getNavigation(navNumber).fromFileNav.methodFqn
        fromNode = pfisGraph.getNode(fromPatchFqn)
        if fromNode['type'] == NodeType.CHANGELOG:
            words = pfisGraph.getNeighborsOfDesiredEdgeTypes(fromPatchFqn, [EdgeType.CONTAINS])
            for word in words:
                pfisGraph.removeEdge(fromPatchFqn, word)


    def __getMethodNodesFromGraph(self, pfisGraph, excludeNode):
        activatedMethodNodes = []
        sortedNodes = []

        for node in self.mapNodesToActivation:
            if node == excludeNode:
                continue

            if pfisGraph.containsNode(node):
                #self.langHelper.excludeMethod(node): this can be added as a node attribute itself
                if pfisGraph.getNode(node)['type'] in [NodeType.METHOD, NodeType.CHANGELOG] \
                        and not self.langHelper.isLibMethodWithoutSource(node):
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

    def predictVariant(self, pfisGraph, fromPatchFqn):
        if not self.langHelper.isChangelogFqn(fromPatchFqn):
            raise Exception("Cannot compute within variant scent for patch type: ", fromPatchFqn)
        else:
            fromPatchCues = set(pfisGraph.getChangelogScent(fromPatchFqn))
            goalWords = set(pfisGraph.getGoalWords())
            common = fromPatchCues.intersection(goalWords)
            if len(common) > 0:
                return fromPatchFqn
            else:
                return None