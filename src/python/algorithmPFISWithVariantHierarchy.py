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

		elif pfisGraph.variantTopology and self._isBetweenVariantNavigation(navPath, navNumber):
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
		fromVariant = self.langHelper.getVariantName(navToPredict.fromFileNav.methodFqn)
		toVariant = self.langHelper.getVariantName(navToPredict.toFileNav.methodFqn)
		return fromVariant != toVariant


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
			variantPrediction = self.computeChangelogScent(pfisGraph, fromPatchFqn)

			if variantPrediction == 0.0: #CHangelog said "Not this variant, but something else!"
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
				return self._predictWithinVariantNavigation(pfisGraph, navPath, navNumber)

	def _predictWithinVariantNavigation(self, pfisGraph, navPath, navNumber):
		return PFIS.makePrediction(self, pfisGraph, navPath, navNumber)

	def computeChangelogScent(self, pfisGraph, fromChangelogFqn):
		self.mapNodesToActivation = {fromChangelogFqn: 0.0}
		self._initializeGoalWords(pfisGraph)

		for _ in range(0, self.NUM_SPREAD):
			for node in self.mapNodesToActivation.keys():
				# Get scent computation nodes for "words in patches", or TF-IDF.
				allNeighbors = pfisGraph.getNeighborsOfDesiredEdgeTypes(node, [EdgeType.CONTAINS])

				# Filter out other patches: this models "TF-IDF between goal words & changelog" single factor.
				changelogScentNeighbors = [n for n in allNeighbors
										   if n == fromChangelogFqn or pfisGraph.getNode(n)['type'] == NodeType.WORD]
				for neighbor in changelogScentNeighbors:
					if neighbor not in self.mapNodesToActivation.keys():
						self.mapNodesToActivation[neighbor] = 0.0
					self.mapNodesToActivation[neighbor] = self.mapNodesToActivation[neighbor] + \
													  self.mapNodesToActivation[node] * self.DECAY_FACTOR

		return self.mapNodesToActivation[fromChangelogFqn]