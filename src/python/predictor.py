from predictions import Predictions
from navpath import NavigationPath

class Predictor(object):
	def __init__(self, graph, navPath):
		self.graph = graph
		self.navPath = navPath
		self.navNumber = -1
		self.endTimeStamp = '0'

	def makeAllPredictions(self, algorithms, outputFolder, topPredictionsFolder=None):

		self.updateGraphByOneNavigation()

		if self.navPath.getLength() < 2:
			raise RuntimeError('makeAllPredictions: Not enough navigations to run predictive algorithms')

		# Build the output data structure
		results = {}
		for algorithm in algorithms:
			results[algorithm.name] = Predictions(algorithm.name, outputFolder, algorithm.fileName, algorithm.includeTop, topPredictionsFolder)

		totalPredictions = self.navPath.getLength() - 1

		for _ in range(1, totalPredictions + 1):
			self.updateGraphByOneNavigation()
			print 'Making predictions for navigation #' + str(self.navNumber) + ' of ' + str(totalPredictions)
			for algorithm in algorithms:
				results[algorithm.name].addPrediction(self.__makePrediction(algorithm))

		print 'Done making predictions.'
		print self.graph.printEntireGraphStats()
		return results

	def __makePrediction(self, predictiveAlgorithm):
		print '\tMaking predictions for ' + predictiveAlgorithm.name + '...'
		return predictiveAlgorithm.makePrediction(self.graph, self.navPath, self.navNumber)

	def __addUnseenButKnownPatch(self):
		if self.navPath.getDefaultNavigation(self.navNumber).isToUnknown():
			actualNavigation = self.navPath.getNavigation(self.navNumber).toFileNav

			if self.graph.containsNode(actualNavigation.methodFqn):
				print "Exception: Unseen method already exists in graph: ", actualNavigation.methodFqn, self.navNumber

			else:
				mostRecentSimilarNav = self.navPath.getPriorNavToSimilarPatchIfAny(self.navNumber)
				if mostRecentSimilarNav is not None:
					self.graph.cloneNode(actualNavigation.methodFqn, mostRecentSimilarNav.methodFqn)

	def __removeTemporarilyAddedNodeIfAny(self):
		if self.navPath.getDefaultNavigation(self.navNumber).isToUnknown():
			currentNav = self.navPath.getNavigation(self.navNumber)
			additionalNode = currentNav.toFileNav.methodFqn
			if self.graph.containsNode(additionalNode):
				self.graph.removeNode(additionalNode)

	def updateGraphByOneNavigation(self):

		if self.navPath.getNavPathType() == NavigationPath.VARIANT_AWARE:
			self.__removeTemporarilyAddedNodeIfAny()

		newEndTimestamp = 0

		if self.navNumber < self.navPath.getLength() - 1:
			self.navNumber += 1
			newEndTimestamp = self.navPath.getNavigation(self.navNumber).toFileNav.timestamp

		self.graph.updateGraphByOneNavigation(self.endTimeStamp, newEndTimestamp)

		self.endTimeStamp = newEndTimestamp

		if self.navPath.getNavPathType() == NavigationPath.VARIANT_AWARE:

			# The actual patch navigated to is not present in graph but we make a prediction,
			# so temporarily add the node in the graph, similar to earlier seen variant.

			self.__addUnseenButKnownPatch()
