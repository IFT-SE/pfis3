from algorithmPFIS import PFIS
from graphAttributes import NodeType

class PFIS3(PFIS):
	def __init__(self, langHelper, name, fileName, history=False, goal = False,
				 decayFactor = 0.85, decaySimilarity=0.85, decayVariant=0.85, decayHistory = 0.9, numSpread = 2,
				 changelogGoalActivation=False, includeTop = False, numTopPredictions=0, verbose = False):
		PFIS.__init__(self, langHelper, name, fileName, history, goal,
				 decayFactor, decaySimilarity, decayVariant, decayHistory, numSpread,
				 changelogGoalActivation, includeTop, numTopPredictions, verbose)

	def spreadActivation(self, pfisGraph,  fromMethodFqn):
		# PFIS3 and CHI'17 PFIS-V do not spread in parallel.
		# Instead the order in which they spread are decide by order yielded by dictionary.keys()
		 for i in range(0, self.NUM_SPREAD):
			print "Spreading {} of {}".format(i + 1, self.NUM_SPREAD)
			for node in self.mapNodesToActivation.keys():
				if pfisGraph.containsNode(node):
					neighbors = pfisGraph.getAllNeighbors(node)

					edgeWeight = 1.0
					if len(neighbors) > 0:
						edgeWeight = 1/len(neighbors)

					for neighbor in neighbors:
						edge_types = pfisGraph.getEdgeTypesBetween(node, neighbor)
						decay_factor = self.getDecayWeight(edge_types)

						if neighbor not in self.mapNodesToActivation.keys():
							self.mapNodesToActivation[neighbor] = 0.0

						self.mapNodesToActivation[neighbor] = self.mapNodesToActivation[neighbor] + \
															  (self.mapNodesToActivation[node] * edgeWeight * decay_factor)
			if self.VERBOSE:
				self.printScores(self.mapNodesToActivation, pfisGraph)