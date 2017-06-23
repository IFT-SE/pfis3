from algorithmPFIS import PFIS
from graphAttributes import NodeType

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
		return self.langHelper.getPatchHierarchy(patchFqn)

	def spreadActivation(self, pfisGraph,  fromMethodFqn=None):
		for i in range(0, self.NUM_SPREAD):
			accumulator = {}
			if i%3 == 0:
				print "Spread to words"
				for node in self.mapNodesToActivation.keys():
					if pfisGraph.getNode(node)['type'] != NodeType.WORD:
						wordNeighbors = [n for n in pfisGraph.getAllNeighbors(node) if pfisGraph.getNode(n)['type'] == NodeType.WORD]
						self.spreadTo(pfisGraph, node, wordNeighbors, self.mapNodesToActivation, accumulator)
			elif i%3 == 1:
				print "Spread word to non-words"
				for node in self.mapNodesToActivation.keys():
					if pfisGraph.getNode(node)['type'] == NodeType.WORD:
						nonWordNeighbors = [n for n in pfisGraph.getAllNeighbors(node) if pfisGraph.getNode(n)['type'] != NodeType.WORD]
						self.spreadTo(pfisGraph, node, nonWordNeighbors, self.mapNodesToActivation, accumulator)
			else:
				for level in range(0, max(NodeType.Levels.values()) + 1):
					print "Spread non-word to non-word nodes from level {0} to same or lower levels in hierarchy".format(level)
					nodes = [n for n in self.mapNodesToActivation.keys() if pfisGraph.getNodeLevel(n) == level]
					accumulator = {}
					for node in nodes:
						neighborsAtSameOrLowerInHierarchy = [n for n in pfisGraph.getAllNeighbors(node) if
							                                     (pfisGraph.getNodeLevel(n) is not None
							                                      and pfisGraph.getNodeLevel(n) >= level)]
						self.spreadTo(pfisGraph, node, neighborsAtSameOrLowerInHierarchy, self.mapNodesToActivation, accumulator)
					self.mapNodesToActivation.update(accumulator)

			self.mapNodesToActivation.update(accumulator)
