from predictions import Predictions
from navpath import NavigationPath

class Predictor(object):
	def __init__(self, graph, navPath, outputFolderPath, topPredictionsPath=None):
		self.graph = graph
		self.navPath = navPath
		self.outputFolder = outputFolderPath
		self.topPredictionsFolder = topPredictionsPath
		self.navNumber = -1
		self.endTimeStamp = '0'

	def makeAllPredictions(self, algorithms):
		self.updateGraphByOneNavigation()
		if self.navPath.getLength() < 2:
			raise RuntimeError('makeAllPredictions: Not enough navigations to run predictive algorithms')

		# Build the output data structure
		results = {}
		for algorithm in algorithms:
			results[algorithm.name] = Predictions(algorithm.name, self.outputFolder, algorithm.fileName,
			                                      algorithm.includeTop, self.topPredictionsFolder)

		totalPredictions = self.navPath.getLength() - 1
		for _ in range(1, totalPredictions + 1):
			self.updateGraphByOneNavigation()
			print 'Making predictions for navigation #' + str(self.navNumber) + ' of ' + str(totalPredictions)
			for algorithm in algorithms:
				prediction = algorithm.makePrediction(self.graph, self.navPath, self.navNumber)
				results[algorithm.name].addPrediction(prediction)

		print 'Done making predictions.'
		print self.graph.printEntireGraphStats()
		return results

	def updateGraphByOneNavigation(self):
		if self.navPath.getNavPathType() == NavigationPath.PFIS_V:
			self.__removeTemporarilyAddedNodeIfAny()

		newEndTimestamp = 0
		if self.navNumber < self.navPath.getLength() - 1:
			self.navNumber += 1
			newEndTimestamp = self.navPath.getNavigation(self.navNumber).toFileNav.timestamp

		print "-----------------------------"
		print "Updating graph... ".format(self.navNumber-1, self.navNumber)

		self.graph.updateGraphByOneNavigation(self.endTimeStamp, newEndTimestamp)

		self.endTimeStamp = newEndTimestamp

		if self.navPath.getNavPathType() == NavigationPath.PFIS_V:
			# The actual patch navigated to is not present in graph but we make a prediction,
			# so temporarily add the node in the graph, similar to earlier seen variant.
			self.__addUnseenButKnownPatch()

	def __addUnseenButKnownPatch(self):
		# If patch is not seen, it can still be known for PFIS-V.
		# So, we add that "unseen, yet known" patch to graph.
		if self.navPath.ifNavToUnseenPatch(self.navNumber):
			actualNavigation = self.navPath.getNavigation(self.navNumber).toFileNav

			if self.graph.containsNode(actualNavigation.methodFqn):
				print "Warning: Unseen method already exists in graph: ", actualNavigation.methodFqn, self.navNumber

			else:
				mostRecentSimilarNav = self.navPath.getPriorNavToSimilarPatchIfAny(self.navNumber)
				if mostRecentSimilarNav is not None:
					print "Clone temporary node {} from {}".format(actualNavigation.methodFqn, mostRecentSimilarNav.methodFqn)

					self.graph.cloneNode(actualNavigation.methodFqn, mostRecentSimilarNav.methodFqn)

	def __removeTemporarilyAddedNodeIfAny(self):
		if self.navPath.ifNavToUnseenPatch(self.navNumber):
			# If graph contains unseen patch, it was because it was known from other variant.
			# Remove this temporary unseen but known patch.
			if self.graph.temporaryMode:
				self.graph.setTemporaryMode(value=False)



