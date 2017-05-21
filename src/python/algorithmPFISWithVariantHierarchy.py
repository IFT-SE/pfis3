from algorithmPFIS import PFIS
from predictions import Prediction
from pfisGraph import EdgeType, NodeType


class PFISWithVariantHierarchy(PFIS):

	def __init__(self, langHelper, name, fileName, history=False, goal=False, \
				 decayFactor = 0.85, decayVariants=0.85, decayHistory = 0.9, numSpread=2,
				 includeTop = False, numTopPredictions=0, verbose=False):
		PFIS.__init__(self, langHelper, name, fileName, history, goal,
						  decayFactor, decayVariants, decayHistory, numSpread,
						  includeTop, numTopPredictions, verbose)

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
		return PFIS.makePrediction(self, pfisGraph, navPath, navNumber)

	def initialize(self, fromMethodFqn, navNumber, navPath, pfisGraph, initializeVariants=False):
		PFIS.initialize(self, fromMethodFqn, navNumber, navPath, pfisGraph)
		if initializeVariants:
			self.__initializeVariants(pfisGraph, fromMethodFqn)


	def __initializeVariants(self, pfisGraph, fromMethodFqn):
		similarPatches = pfisGraph.getNeighborsOfDesiredEdgeTypes(fromMethodFqn, [EdgeType.VARIANT_OF])
		for node in similarPatches:
			if node not in self.mapNodesToActivation.keys():
				self.mapNodesToActivation[node] = 0.0
			else:
				self.mapNodesToActivation[node] = self.mapNodesToActivation[node] + 10.0


	def __removeWordsFromAbandonedChangelogs(self, pfisGraph, navPath, navNumber):
		fromPatchFqn = navPath.getNavigation(navNumber).fromFileNav.methodFqn
		fromNode = pfisGraph.getNode(fromPatchFqn)
		if fromNode['type'] == NodeType.CHANGELOG:
			words = pfisGraph.getNeighborsOfDesiredEdgeTypes(fromPatchFqn, [EdgeType.CONTAINS])
			for word in words:
				pfisGraph.removeEdge(fromPatchFqn, word)

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