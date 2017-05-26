from algorithmPFIS import PFIS
from predictions import Prediction
from pfisGraph import EdgeType, NodeType


class PFISWithVariantHierarchy(PFIS):

	def __init__(self, langHelper, name, fileName, history=False, goal=False, \
	             decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread=2,
	             includeTop = False, numTopPredictions=0, verbose=False):
		PFIS.__init__(self, langHelper, name, fileName, history, goal,
		              decayFactor, decaySimilarity, decayVariant, decayHistory, numSpread,
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

		fromMethodFqn = navToPredict.fromFileNav.methodFqn
		methodToPredict = navToPredict.toFileNav.methodFqn

		if pfisGraph.variantTopology and self._isBetweenVariantNavigation(fromMethodFqn, methodToPredict):
			prediction = self._predictBetweenVariantNavigation(pfisGraph, navPath, navNumber)
			if prediction is None:
				raise Exception("SS, BP: Investigate why, else this might be another case of unknown")
			return prediction

		else:
			prediction = self._predictWithinVariantNavigation(pfisGraph, navPath, navNumber)
			if prediction is None:
				raise Exception("SS, BP: Investigate why, else this might be another case of unknown")
			return prediction

	def _isBetweenVariantNavigation(self, fromFqn, toFqn):
		fromVariant = self.langHelper.getVariantName(fromFqn)
		toVariant = self.langHelper.getVariantName(toFqn)
		return fromVariant != toVariant


	def _predictBetweenVariantNavigation(self, pfisGraph, navPath, navNumber):
		navToPredict = navPath.getNavigation(navNumber)
		fromPatchFqn = navToPredict.fromFileNav.methodFqn
		toPatchFqn = navToPredict.toFileNav.methodFqn

		fromVariant = self.langHelper.getVariantName(fromPatchFqn)
		toVariant = self.langHelper.getVariantName(toPatchFqn)

		fromPatchType = pfisGraph.getNode(fromPatchFqn)['type']

		if fromPatchType in [NodeType.METHOD, NodeType.OUTPUT]:
			return self._predictWithinVariantNavigation(pfisGraph, navPath, navNumber)

		elif fromPatchType == NodeType.CHANGELOG:
			self.activatePatchWithGoalWordSimilarity(pfisGraph, fromPatchFqn, True)
			variantPrediction = self.mapNodesToActivation[fromPatchFqn]

			if variantPrediction == 0.0: #Changelog said "Not this variant, but something else!"
				if toVariant == fromVariant:
					# Person went into that variant -- Between-variant MISS
					return Prediction(navNumber, 888888, 0, 0,
								  str(navToPredict.fromFileNav),
								  str(navToPredict.toFileNav),
								  navToPredict.toFileNav.timestamp)
			return self._predictWithinVariantNavigation(pfisGraph, navPath, navNumber)

	def _predictWithinVariantNavigation(self, pfisGraph, navPath, navNumber):
		return PFIS.makePrediction(self, pfisGraph, navPath, navNumber)
