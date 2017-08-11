from predictiveAlgorithm import PredictiveAlgorithm
from predictions import Prediction
from graphAttributes import *


class HierarchySingleFactor(PredictiveAlgorithm):

	def __init__(self, langHelper, name, fileName, includeTop = False, numTopPredictions=0):
		PredictiveAlgorithm.__init__(self, langHelper, name, fileName, includeTop, numTopPredictions)

	def makePrediction(self, pfisGraph, navPath, navNumber):
		if navNumber < 1 or navNumber >= navPath.getLength():
			raise RuntimeError('makePrediction: navNumber must be > 0 and less than the length of navPath')

		navToPredict = navPath.getNavigation(navNumber)
		fromMethodFqn = navToPredict.fromFileNav.methodFqn
		methodToPredict = navToPredict.toFileNav.methodFqn

		sortedRanksMethodsOnly = []

		if not navToPredict.isToUnknown() and pfisGraph.containsNode(methodToPredict):
			nodeDistances = self.computeCostLevelWise(fromMethodFqn, pfisGraph)

			methodToPredictEquiv = pfisGraph.getFqnOfEquivalentNode(methodToPredict)
			if methodToPredictEquiv in nodeDistances.keys():
				result = nodeDistances[methodToPredictEquiv]

				sortedRanks = sorted(nodeDistances, key = lambda node: nodeDistances[node])
				sortedRanksMethodsOnly = self.getRanksForMethodsOnly(sortedRanks, pfisGraph)

				firstIndex = self.getFirstIndex(sortedRanksMethodsOnly, nodeDistances, result)
				lastIndex = self.getLastIndex(sortedRanksMethodsOnly, nodeDistances, result)
				numTies = lastIndex - firstIndex + 1
				rankWithTies = self.getRankConsideringTies(firstIndex + 1, numTies)
				topPredictions = []

				if self.includeTop:
					topPredictions = self.getTopPredictions(sortedRanksMethodsOnly, nodeDistances)

				return Prediction(navNumber, rankWithTies, len(sortedRanksMethodsOnly), numTies,
						   fromMethodFqn,
						   methodToPredict,
						   navToPredict.toFileNav.timestamp,
						   topPredictions)

		return Prediction(navNumber, 999999, len(sortedRanksMethodsOnly), 0,
						   str(navToPredict.fromFileNav),
						   str(navToPredict.toFileNav),
						   navToPredict.toFileNav.timestamp)

	def computeCostLevelWise(self, fromMethodFqn, pfisGraph):
		nodeDistances = {}

		hierarchy = self.langHelper.getPatchHierarchy(fromMethodFqn)
		for item in hierarchy:
			print item
			nodeDistances[item] = 0

		minLevel = min(NodeType.Levels.values())
		maxLevel = max(NodeType.Levels.values())

		for level in range(minLevel, maxLevel + 1):
			print "----------------\nLevel: ", level
			for node in nodeDistances.keys():
				if pfisGraph.containsNode(node) and pfisGraph.getNodeLevel(node) == level:
					containmentNeighbors = pfisGraph.getNeighborsOfDesiredEdgeTypes(node, [EdgeType.CONTAINS])
					lowerLevelContainmentNeighbors = [n for n in containmentNeighbors if
					                                  pfisGraph.getNodeLevel(n) > level]
					for neighbor in lowerLevelContainmentNeighbors:
						distance = pfisGraph.getDistance(fromMethodFqn, neighbor)
						if neighbor not in nodeDistances.keys() or distance < nodeDistances[neighbor]:
							nodeDistances[neighbor] = distance
							print "Level {0} {1} to Level {2} {3}: Dist {4}".format(pfisGraph.getNodeLevel(node), node, pfisGraph.getNodeLevel(neighbor), neighbor, distance)

		return nodeDistances