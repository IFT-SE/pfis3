from algorithmPFIS import PFIS

class PFISHierarchy(PFIS):
	def __init__(self, langHelper, name, fileName, history=False, goal = False,
                 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
                 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
		PFIS.__init__(self, langHelper, name, fileName, history, goal,
                 decayFactor, decaySimilarity, decayVariant, decayHistory, numSpread,
                 changelogGoalActivation, includeTop, numTopPredictions, verbose)

	def setPatchActivation(self, pfisGraph, patchFqn, value):
		hierarchyOfNodes = self.getEntireHierarchy(patchFqn, pfisGraph)
		for nodeFqn in hierarchyOfNodes:
			PFIS.setPatchActivation(self, pfisGraph, nodeFqn, value)

	def getEntireHierarchy(self, patchFqn, pfisGraph):
		return self.langHelper.splitFqn(patchFqn)
