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

		return self._predictNavigationConsideringHierarchy(pfisGraph, navPath, navNumber)

	def _predictNavigationConsideringHierarchy(self, pfisGraph, navPath, navNumber):
		navToPredict = navPath.getNavigation(navNumber)
		fromPatchFqn = navToPredict.fromFileNav.methodFqn
		toPatchFqn = navToPredict.toFileNav.methodFqn

		fromVariant = self.langHelper.getVariantName(fromPatchFqn)
		toVariant = self.langHelper.getVariantName(toPatchFqn)

		fromPatchType = pfisGraph.getNode(fromPatchFqn)['type']

		if fromPatchType in [NodeType.METHOD, NodeType.OUTPUT]:
			return self._predictPatchesWithoutConsideringHierarchy(pfisGraph, navPath, navNumber)

		elif fromPatchType == NodeType.CHANGELOG:
			self.activatePatchWithGoalWordSimilarity(pfisGraph, fromPatchFqn, True)
			changelogGoalWordActivation = self.mapNodesToActivation[fromPatchFqn]

			if changelogGoalWordActivation == 0.0:
				if fromVariant != toVariant:
					return self._predictPatchesWithoutConsideringHierarchy(pfisGraph, navPath, navNumber)

				if fromVariant == toVariant:
					# Person went into that variant, even when changelog was irrelevant to goal words. Prediction MISS.
					print "Predicted won't enter variant, but programmer entered! MISS: 888888."
					return Prediction(navNumber, 888888, 0, 0,
								  str(navToPredict.fromFileNav),
								  str(navToPredict.toFileNav),
								  navToPredict.toFileNav.timestamp)

			if changelogGoalWordActivation > 0.0:
				if fromVariant == toVariant:
					return self._predictPatchesWithoutConsideringHierarchy(pfisGraph, navPath, navNumber)

				if fromVariant != toVariant:
					print "Predicted should enter variant, but programmer went elsewhere! MISS: 888888."
					return Prediction(navNumber, 888888, 0, 0,
									  str(navToPredict.fromFileNav),
									  str(navToPredict.toFileNav),
									  navToPredict.toFileNav.timestamp)


	def _predictPatchesWithoutConsideringHierarchy(self, pfisGraph, navPath, navNumber):
		return PFIS.makePrediction(self, pfisGraph, navPath, navNumber)
