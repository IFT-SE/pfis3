from algorithmPFIS import PFIS
from graphAttributes import NodeType, EdgeType

class PFISHierarchy(PFIS):
	def __init__(self, langHelper, name, fileName, history=False, goal = False,
				 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
				 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
		PFIS.__init__(self, langHelper, name, fileName, history, goal,
				 decayFactor, decaySimilarity, decayVariant, decayHistory, numSpread,
				 changelogGoalActivation, includeTop, numTopPredictions, verbose)

	def setPatchActivation(self, pfisGraph, patchFqn, value):
		activation = value
		# hierarchyOfNodes = self.langHelper.getPatchHierarchy(patchFqn)
		hierarchyOfNodes = pfisGraph.getPatchHierarchy(patchFqn)
		hierarchyOfNodes.reverse()

		if pfisGraph.optionToggles['excludeHierarchyLevels']:
			hierarchyOfNodes = [hierarchyOfNodes[0], hierarchyOfNodes[-1]]

		for nodeFqn in hierarchyOfNodes:
			# If graph contains that node (can be excluded, such as package nodes), activate it.
			if pfisGraph.containsNode(nodeFqn):
				PFIS.setPatchActivation(self, pfisGraph, nodeFqn, activation)
				# activation = activation * 0.85

	def spreadActivation(self, pfisGraph,  fromMethodFqn):
		for i in range(0, self.NUM_SPREAD):
			accumulator = {}
			if i%3 == 0:
				if self.VERBOSE:
					print "Spread non-words to words"
				for node in self.mapNodesToActivation.keys():
					if pfisGraph.getNode(node)['type'] != NodeType.WORD:
						wordNeighbors = [n for n in pfisGraph.getAllNeighbors(node) if pfisGraph.getNode(n)['type'] == NodeType.WORD]
						self.spreadTo(pfisGraph, node, wordNeighbors, self.mapNodesToActivation, accumulator)
			elif i%3 == 1:
				for level in range(0, max(NodeType.Levels.values()) + 1):
					if self.VERBOSE:
						print "Spread non-word to non-word nodes from level {0} to same or lower levels in hierarchy".format(level)
					nodes = [n for n in self.mapNodesToActivation.keys() if pfisGraph.getNodeLevel(n) == level]
					accumulator = {}
					for node in nodes:
						neighborsAtSameOrLowerInHierarchy = [n for n in pfisGraph.getAllNeighbors(node) if
																 (pfisGraph.getNodeLevel(n) is not None
																  and pfisGraph.getNodeLevel(n) >= level)]
						self.spreadTo(pfisGraph, node, neighborsAtSameOrLowerInHierarchy, self.mapNodesToActivation, accumulator)
					self.mapNodesToActivation.update(accumulator)
			else:
				if self.VERBOSE:
					print "Spread word to non-words"
				for node in self.mapNodesToActivation.keys():
					if pfisGraph.getNode(node)['type'] == NodeType.WORD:
						nonWordNeighbors = [n for n in pfisGraph.getAllNeighbors(node) if pfisGraph.getNode(n)['type'] != NodeType.WORD]
						self.spreadTo(pfisGraph, node, nonWordNeighbors, self.mapNodesToActivation, accumulator)

			self.mapNodesToActivation.update(accumulator)

	def spreadTo(self, pfisGraph, spreadFrom, neighborsToSpread, priorSpreadResultant, accumulator):
		spreadFromNodeType = pfisGraph.getNode(spreadFrom)['type']

		edgeWeight = 1.0
		if len(neighborsToSpread) > 0:
			edgeWeight = 1.0 / len(neighborsToSpread)

		for neighbor in neighborsToSpread:
			decay_factor = self.getDecayWeight(spreadFrom, neighbor, pfisGraph)
			distance = 1.0
			# If spreading non-word to non-word, get the cost (distance) of navigating to "to" from current patch
			if spreadFromNodeType != NodeType.WORD and pfisGraph.getNode(neighbor)['type'] != NodeType.WORD:
				distance = pfisGraph.getDistance(self.currentNode, neighbor)

			if neighbor not in accumulator:
				if neighbor in self.mapNodesToActivation.keys():
					accumulator[neighbor] = self.mapNodesToActivation[neighbor]
				else:
					accumulator[neighbor] = 0.0

			neighborWeightBeforeSpread = accumulator[neighbor]
			neighborWeightAfterSpreading = neighborWeightBeforeSpread + (priorSpreadResultant[spreadFrom] * edgeWeight * decay_factor)/distance
			accumulator[neighbor] = neighborWeightAfterSpreading

			if self.VERBOSE:
				print '{} to {}: {} + ({}*{}*{}) = {}'.format(spreadFrom, neighbor,
																   neighborWeightBeforeSpread,
																   priorSpreadResultant[spreadFrom], edgeWeight, decay_factor,
																   neighborWeightAfterSpreading)